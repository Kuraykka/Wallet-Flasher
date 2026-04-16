# ⚡ Discord ERC20 Transaction Bot

A simple Discord bot to send ERC20 token transactions on Ethereum using slash commands. Built with `discord.py` and `web3.py`.

---

## 🇬🇧 English

### 🚀 Features

* Send ERC20 tokens via Discord
* Supports USDT, USDC, DAI
* Async execution
* Logging system
* Multi-RPC support

---

### ⚙️ Setup

Create a `.env` file:

```env
DISCORD_BOT_TOKEN=your_token_here
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python startbot.py
```

---

### 🤖 Commands

#### `/ping`

Check if the bot is online.

#### `/logs`

Show latest logs (last 10 events).

#### `/send`

Send ERC20 tokens.

**Parameters:**

* `token` → USDT / USDC / DAI
* `amount` → Amount to send
* `recipient` → Ethereum address
* `rebroadcast_seconds` (optional)

**Example:**

```
/send token:USDT amount:10 recipient:0xABC... rebroadcast_seconds:30
```

---

### 🧠 How it works

1. Receives a command from Discord
2. Builds an ERC20 transfer transaction
3. Signs it with a private key
4. Sends it to Ethereum RPC nodes
5. Logs the result

---

### ⚠️ Security

Private key is stored in code.
**Do NOT use real funds.**

---

## 🇪🇸 Español

### 🚀 Características

* Envío de tokens ERC20 desde Discord
* Soporte para USDT, USDC y DAI
* Ejecución asíncrona
* Sistema de logs
* Soporte para múltiples RPC

---

### ⚙️ Configuración

Crea un archivo `.env`:

```env
DISCORD_BOT_TOKEN=tu_token_aqui
```

Instala dependencias y ejecuta:

```bash
pip install -r requirements.txt
python bot.py
```

---

### 🤖 Comandos

#### `/ping`

Verifica si el bot está activo.

#### `/logs`

Muestra los últimos logs (10 eventos).

#### `/send`

Envía tokens ERC20.

**Parámetros:**

* `token` → USDT / USDC / DAI
* `amount` → Cantidad
* `recipient` → Dirección Ethereum
* `rebroadcast_seconds` (opcional)

**Ejemplo:**

```
/send token:USDT amount:10 recipient:0xABC... rebroadcast_seconds:30
```

---

### 🧠 Funcionamiento

1. Recibe un comando
2. Construye la transacción ERC20
3. La firma con una clave privada
4. La envía a nodos RPC
5. Guarda logs

---

### ⚠️ Seguridad

La clave privada está en el código.
**NO usar fondos reales.**
