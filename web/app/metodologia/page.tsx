import { SliceShell } from '@/components/SliceShell'
import { loadSliceCoverage } from '@/lib/api'
import { METHOD_VERSION } from '@/lib/copy'
import { routes } from '@/lib/routes'
import type { Metadata } from 'next'

export const dynamic = 'force-dynamic'
export const metadata: Metadata = { title: 'Metodologia' }

export default async function MetodologiaPage() {
  const coverage = await loadSliceCoverage()
  const version = coverage.methodologyVersion || METHOD_VERSION
  return (
    <SliceShell coverage={coverage}>
      <div className="method">
        <p className="kicker">Versão {version}</p>
        <h1>Metodologia do explorador</h1>
        <p className="lede">
          Fase 2: busca, listagem e ficha.
          Sem pontuação, sem classificação de órgãos ou fornecedores e sem alertas públicos.
          Os sinais internos abaixo descrevem o recorte 0.2 e não abrem ficha pública.
        </p>
        <div className="notice notice-caveat">
          <p>
            Em juízo, o fracionamento da contratação exige dolo específico.
            O sinal interno de fracionamento é um indício de agregado anual do mesmo objeto
            frente aos limiares do decreto do Art. 75, e não um veredito.
          </p>
          <p>
            Sócios em comum não são, por si sós, ilícitos, conforme os Acórdãos 297/2009,
            1.793/2011 e 2.803/2016 do TCU.
          </p>
          <p>
            Um desvio de preço não é, por si só, um ilícito.
            A precisão do método ingênuo da Fase 0 neste recorte é 9%.
            Sinais públicos permanecem fechados.
            Nada acusatório é publicado antes de 25 de outubro de 2026.
          </p>
        </div>
        <section className="section">
          <p className="kind">qty_unit_price_neq_total</p>
          <h2>Quantidade e exclusões de qualidade</h2>
          <p>
            O sinal nasce quando quantidade vezes preço unitário diverge do total além de 0,02 ou 0,2%.
            O mesmo critério vira exclusão de qualidade de dado e tira o item do pool de anomalia de preço.
            Outras exclusões são deslocamento decimal, colapso em quantidade 1, valor nulo ou negativo,
            linha duplicada e magnitude fora do catálogo.
            Exclusão não é alerta público.
            O item permanece no explorador.
          </p>
        </section>
        <section className="section">
          <p className="kind">sanctioned_ceis_cnep</p>
          <h2>CEIS e CNEP na janela da homologação</h2>
          <p>
            O cruzamento usa o CNPJ do fornecedor e as listas CEIS e CNEP da CGU.
            O sinal só nasce quando a data de homologação cai dentro da vigência da sanção.
            Fonte e janela ficam no landing interno.
            O explorador não lê essa fonte.
          </p>
        </section>
        <section className="section">
          <p className="kind">cnpj_age · cnpj_age_info</p>
          <h2>Idade do CNPJ</h2>
          <p>
            O sinal de idade nasce quando a homologação ocorre em menos de 90 dias após a abertura do CNPJ.
            O sinal informativo nasce quando essa idade está entre 90 e 365 dias.
            Idade maior que 365 dias não gera sinal.
            Datas ausentes ou invertidas são ignoradas.
          </p>
        </section>
        <section className="section">
          <p className="kind">fracionamento · fracionamento_cluster</p>
          <h2>Fracionamento</h2>
          <p>
            O sinal de fracionamento agrega dispensas do mesmo órgão, mesma classe e mesmo ano.
            Ele nasce quando cada compra fica abaixo do limiar do decreto daquele ano e a soma
            ultrapassa o Art. 75.
            O agrupamento pede ao menos três dispensas na última décima do limiar, com datas em
            janela de 90 dias.
            Os valores do limiar vêm da tabela oficial de decretos, não de um número solto no código.
          </p>
        </section>
        <section className="section">
          <p className="kind">cnae_mismatch</p>
          <h2>CNAE fora da allow-list da classe</h2>
          <p>
            O sinal nasce em item de material homologado quando a classe CATMAT tem prefixos
            CNAE mapeados e nenhum CNAE do vencedor, principal ou secundário, começa com esses prefixos.
            Classe ausente, CNAE ausente e classe sem mapeamento não geram sinal e permanecem no denominador.
            Linha de serviço fica de fora.
            Este sinal tem risco alto de falso positivo.
            Ele fica fora do conjunto de novembro até uma amostragem posterior cruzar o limiar.
            Não é alerta público.
          </p>
        </section>
        <section className="section">
          <p className="kind">retroactive_edit</p>
          <h2>Edição depois da publicação</h2>
          <p>
            O sinal compara snapshots do mesmo registro no landing.
            Ele nasce quando preço, quantidade ou fornecedor muda depois da publicação ou da homologação.
            Mudança só de descrição não gera sinal.
            Snapshot anterior à publicação não gera sinal.
          </p>
        </section>
        <div className="prose">
          <p>As rotas lidas são GET /api/orgaos, /api/fornecedores, /api/contratacoes e /api/items, com detalhe por id.</p>
          <p>Listas usam PageRequest com skip e take no servidor. Não há ordenação por pontuação.</p>
          <p>Fichas leem o warehouse a cada pedido.</p>
          <p>CPF chega mascarado da origem e não é exibido em campo próprio.</p>
          <p>Não há lista de partido nem de político.</p>
          <p>O texto público publica número, fonte e snapshot. Não usa rótulo de veredito.</p>
          <p>O warehouse é o contrato. O Python nunca chama o C#. O C# nunca executa um detector.</p>
          <p>
            A cobertura do recorte está em <a href={routes.cobertura}>Cobertura</a>.
          </p>
        </div>
      </div>
    </SliceShell>
  )
}
