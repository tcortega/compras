#!/bin/sh
# Keep compose container-to-container traffic on a stock Linux Docker engine.
# When dockerd already manages iptables, this is a no-op besides ip_forward.
# When dockerd was started with iptables=false, apply durable ICC here so
# docker compose up does not depend on a host one-liner.

set -eu

OK_FILE=/tmp/compras-icc-ok
SYSCTL_FILE=/etc/sysctl.d/99-compras-icc.conf
COMMENT=compras-icc

sysctl_set() {
  key=$1
  val=$2
  path=/proc/sys/$(echo "$key" | tr . /)
  if [ -e "$path" ]; then
    sysctl -w "$key=$val" >/dev/null
  fi
}

ipt_try() {
  cmd=$1
  shift
  command -v "$cmd" >/dev/null 2>&1 || return 1
  "$cmd" "$@"
}

has_docker_chain() {
  ipt_try iptables-legacy -nL DOCKER >/dev/null 2>&1 && return 0
  ipt_try iptables-nft -nL DOCKER >/dev/null 2>&1 && return 0
  ipt_try iptables -nL DOCKER >/dev/null 2>&1 && return 0
  return 1
}

ipt_apply() {
  if ipt_try iptables-legacy -nL FORWARD >/dev/null 2>&1; then
    iptables-legacy "$@"
    return
  fi
  if ipt_try iptables-nft -nL FORWARD >/dev/null 2>&1; then
    iptables-nft "$@"
    return
  fi
  iptables "$@"
}

ensure_icc_rule() {
  cidr=$1
  if ipt_apply -C FORWARD -s "$cidr" -d "$cidr" -m comment --comment "$COMMENT" -j ACCEPT >/dev/null 2>&1; then
    return 0
  fi
  ipt_apply -I FORWARD -s "$cidr" -d "$cidr" -m comment --comment "$COMMENT" -j ACCEPT >/dev/null 2>&1
}

add_bridge_icc_rules() {
  added=0
  for dev in $(ls /sys/class/net); do
    case "$dev" in
      docker0|br-*) ;;
      *) continue ;;
    esac
    cidrs=$(ip -o -4 route show dev "$dev" proto kernel 2>/dev/null | awk '{print $1}')
    for cidr in $cidrs; do
      case "$cidr" in
        */*) ;;
        *) continue ;;
      esac
      if ensure_icc_rule "$cidr"; then
        added=1
      fi
    done
  done
  [ "$added" = 1 ]
}

merge_daemon_json() {
  snippet=/opt/compras/docker-daemon.json
  target=/etc/docker/daemon.json
  if [ ! -f "$snippet" ] || [ ! -d /etc/docker ] || [ ! -w /etc/docker ]; then
    return 0
  fi
  if [ ! -f "$target" ]; then
    cp "$snippet" "$target" || true
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  if jq -s '.[0] * .[1]' "$target" "$snippet" > /tmp/compras-docker-daemon.json 2>/dev/null; then
    if ! cmp -s /tmp/compras-docker-daemon.json "$target"; then
      cp /tmp/compras-docker-daemon.json "$target" || true
    fi
  fi
}

write_sysctl() {
  if [ ! -d /etc/sysctl.d ] || [ ! -w /etc/sysctl.d ]; then
    return 0
  fi
  if [ "$1" = "full" ]; then
    cat > "$SYSCTL_FILE" << 'EOF'
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 0
net.bridge.bridge-nf-call-ip6tables = 0
EOF
    return 0
  fi
  cat > "$SYSCTL_FILE" << 'EOF'
net.ipv4.ip_forward = 1
EOF
}

ensure() {
  sysctl_set net.ipv4.ip_forward 1
  merge_daemon_json

  if has_docker_chain; then
    write_sysctl forward
    return 0
  fi

  sysctl_set net.bridge.bridge-nf-call-iptables 0 || true
  sysctl_set net.bridge.bridge-nf-call-ip6tables 0 || true
  write_sysctl full

  nf_path=/proc/sys/net/bridge/bridge-nf-call-iptables
  if [ -e "$nf_path" ] && [ "$(cat "$nf_path")" = "0" ]; then
    return 0
  fi
  add_bridge_icc_rules
}

if ! ensure; then
  echo "compras icc: dockerd is not managing iptables and ICC could not be applied" >&2
  exit 1
fi

: > "$OK_FILE"

while true; do
  ensure || echo "compras icc: re-apply failed" >&2
  sleep 30
done
