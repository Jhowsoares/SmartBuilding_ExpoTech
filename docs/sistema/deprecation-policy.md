# ⏳ Política de Depreciação e Ciclo de Vida da API

Esta política estabelece as diretrizes, prazos e padrões de comunicação para a descontinuação, substituição e desligamento definitivo (*sunset*) de recursos, endpoints ou versões legadas da REST API do **Smart Building**.

---

## 📌 1. Ciclo de Vida de um Endpoint

Todo recurso que entra em obsolescência passará obrigatoriamente por três fases bem definidas:

1. **Active (Ativo):** Versão atual recomendada para consumo em produção.
2. **Deprecated (Depreciado):** O recurso continua operacional, mas seu uso não é mais recomendado para novas integrações. O backend passa a retornar o cabeçalho HTTP `Deprecation`.
3. **Sunset (Desativado):** O endpoint deixa de responder permanentemente, retornando códigos de erro HTTP adequados (`410 Gone` ou `404 Not Found`).

---

## 📅 2. Prazos e Comunicação (Grace Period)

* **Aviso Prévio:** Um endpoint será marcado como depreciado com no mínimo **6 meses de antecedência** do seu desligamento definitivo.
* **Cabeçalhos HTTP (RFC 8594):** Durante o período de depreciação, todas as respostas do endpoint incluirão os seguintes cabeçalhos padronizados:
  * `Deprecation: date="YYYY-MM-DD"` *(Data em que o recurso foi marcado como obsoleto)*
  * `Sunset: date="YYYY-MM-DD"` *(Data programada para o desligamento definitivo)*

---

## 🧪 3. Exemplo Prático de Governança

Para exemplificação no contrato OpenAPI, a rota de histórico legado de sensores (`/api/v1/sensors/{sensor_id}/data`) está sinalizada simulando este ciclo de vida:

| Marco | Data Programada | Status do Endpoint |
| :--- | :--- | :--- |
| **Data de Depreciação** | `2027-01-01` | Emite cabeçalho `Deprecation` |
| **Data de Sunset** | `2027-06-01` | Desligamento definitivo (`410 Gone`) |

