# 🏛️ Sistema — Especificação e Arquitetura Técnica

Esta seção contém a documentação detalhada da arquitetura, contratos de API, especificações de mensageria IoT e modelos de dados do ecossistema **Smart Building**.

---

## 📑 Módulos e Especificações

| Documento | Descrição Técnica | Foco de Engenharia |
| :--- | :--- | :--- |
| **[architecture.md](architecture.md)** | Stack de tecnologias, diagrama C4, fluxo de dados e decisões de design | Arquitetura de Software / C4 |
| **[project-structure.md](project-structure.md)** | Estrutura de diretórios, serviços Docker e separação de responsabilidades | Organização & Padrões |
| **[api.md](api.md)** | Endpoints REST, autenticação JWT, papéis de usuário (RBAC) e OpenAPI | Backend & Contratos |
| **[mqtt.md](mqtt.md)** | Tópicos de mensageria, estrutura de payloads JSON e QoS | IoT & Ingestão Assíncrona |
| **[business-rules.md](business-rules.md)** | Motor de regras de automação (RN01–RN10) e modelo preditivo de consumo ML | Regras de Negócio & ML |
| **[hardware-esp32.md](hardware-esp32.md)** | Firmware C++, pinagem dos sensores, atuações e integração Bluetooth | Hardware & Embedded C++ |
| **[network-expotech.md](network-expotech.md)** | Arquitetura de rede, tunelamento para nós remotos e segurança de borda | Infraestrutura & Redes |
| **[deprecation-policy.md](deprecation-policy.md)** | Diretrizes de ciclo de vida e versionamento da API `/v1` | Versionamento & Governança |

---

🔗 **Recursos e Contratos:**
* **Contrato OpenAPI 3.0:** [`openapi.yaml`](../openapi.yaml)
* **Índice Geral de Documentação:** [`docs/README.md`](../README.md)