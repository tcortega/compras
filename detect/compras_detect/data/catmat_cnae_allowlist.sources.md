# Fontes da allow-list CATMAT × CNAE

A tabela versionada `catmat_cnae_allowlist.csv` guarda prefixos CNAE plausíveis por classe CATMAT de 4 dígitos.
Os nomes de classe CATMAT seguem o catálogo oficial em https://catalogo.compras.gov.br/ e o estilo catalogo.gov.br / compras.gov.br.
Os prefixos CNAE de 2 dígitos são divisões e os de 5 dígitos são a classe CNAE 2.0 (quatro dígitos mais o dígito verificador), conforme https://concla.ibge.gov.br/busca-online-cnae.html.
A classe 10.61-9 e a subclasse 1061-9/01 (beneficiamento de arroz) estão em https://concla.ibge.gov.br/busca-online-cnae.html?classe=10619&tipo=cnae&versao=10&view=classe.
A classe 46.32-0 e a subclasse 4632-0/01 (atacado de cereais beneficiados) estão em https://concla.ibge.gov.br/busca-online-cnae.html?classe=46320&tipo=cnae&versao=10&view=classe.
A classe 46.47-8 e a subclasse 4647-8/01 (atacado de papelaria) estão em https://concla.ibge.gov.br/busca-online-cnae.html?classe=46478&tipo=cnae&versao=10&view=classe.
A lista é conservadora: classe sem prefixo mapeado não gera sinal.
O modo fixture lê só este CSV e não consulta esses hosts.
