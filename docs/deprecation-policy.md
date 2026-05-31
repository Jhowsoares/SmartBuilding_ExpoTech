# Política de Depreciação e Ciclo de Vida da API (Critério 5)

Esta política estabelece as diretrizes e prazos para a descontinuação, substituição e desligamento definitivo de recursos, endpoints ou versões legadas da API do Smart Building.

## 1. Ciclo de Vida de um Endpoint
Todo recurso que entra em obsolescência passará obrigatoriamente por três fases:

1. **Active (Ativo):** Versão atual recomendada para consumo em produção.
2. **Deprecated (Depreciado):** O recurso continua totalmente operacional, mas seu uso não é mais recomendado. Novos clientes não devem adotá-lo. É emitido o cabeçalho HTTP `Deprecation`.
3. **Sunset (Desativado):** O endpoint deixa de responder permanentemente, retornando códigos de erro adequados (como `410 Gone` ou `404 Not Found`).

## 2. Prazos e Comunicação (Grace Period)
* **Aviso Prévio:** Um endpoint será marcado como depreciado com no mínimo **6 meses** de antecedência do seu desligamento definitivo (*Sunset*).
* **Documentação via Cabeçalhos HTTP:** Durante o período de depreciação, todas as requisições feitas ao endpoint retornarão os cabeçalhos padrão descritos na RFC 8594:
  * `Deprecation: date="AAAA-MM-DD"` (Data em que virou obsoleto)
  * `Sunset: date="AAAA-MM-DD"` (Data programada para o desligamento definitivo)

## 3. Exemplo de Implementação Prática
Para fins de validação da banca examinadora, a rota legada de histórico de sensores (`/api/v1/sensors/{sensor_id}/data`) já está documentada no contrato OpenAPI simulando este ciclo de vida com os seguintes marcos cronológicos:
* **Data de Depreciação:** 2027-01-01
* **Data de Sunset (Desligamento):** 2027-06-01