FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY global.json Directory.Build.props Directory.Build.targets Directory.Packages.props Compras.sln ./
COPY docs/guidelines/BannedSymbols.txt docs/guidelines/BannedSymbols.txt
COPY api api
RUN dotnet publish api/Api/Api.csproj -c Release -o /out --no-self-contained

FROM mcr.microsoft.com/dotnet/aspnet:8.0
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /out .
ENV ASPNETCORE_ENVIRONMENT=Production
EXPOSE 5080
ENTRYPOINT ["dotnet", "Api.dll"]
