# x402 Research Agent

> An autonomous multi-agent research system that can discover, hire, and pay for external AI services using the x402 payment protocol.

Built for **Brainwave 2026 — Guru Gobind Singh Indraprastha University (GGSIPU)**.

---

## Overview

Researching complex topics manually can be slow and repetitive. Finding relevant sources, comparing information, fact-checking claims, and putting everything together takes significant time.

This project explores a different approach:

**What if an AI could do the research itself, and even pay for the services it needs?**

The x402 Research Agent is a multi-agent research system that decomposes complex questions into smaller tasks, delegates them to specialized agents and external services, uses **x402 micropayments** to access paid capabilities, fact-checks the collected information, and synthesizes everything into a cited research report.

The goal is to move from:

**AI that uses tools**

to:

**AI that can autonomously acquire and use the tools it needs.**

---

## Why I Built This

Manually researching things for myself became increasingly tedious, so I decided to build something to solve the problem.

While learning about AI during the recent AI boom, I explored LLMs, AI agents, orchestration, tool calling, and multi-agent systems. This led me to the idea of splitting research into specialized tasks that could be handled autonomously.

While exploring agent infrastructure, I came across **x402**, an HTTP-native payment protocol that allows services to require payment directly through HTTP requests.

That created an interesting possibility:

> **What if the research agent could not only use external services, but also pay for them on its own?**

This project is an exploration of that idea.

---

## Core Features

### Autonomous Research

- Decomposes complex research questions into smaller tasks.
- Uses specialized agents for searching, analysis, fact-checking, and synthesis.

### x402-Powered Payments

- Detects when an external service requires payment.
- Automatically handles the x402 payment flow and pays on a per-request basis.

### Multi-Agent Orchestration

- Coordinates multiple specialized agents.
- Allows independent research tasks to be executed and combined into a single result.

### Fact Checking

- Cross-checks information collected from different sources.
- Helps reduce hallucinations and unsupported claims.

### Cited Reports

- Synthesizes the collected information.
- Produces a structured research report with supporting sources.

---

## How x402 Fits In

Traditional AI agents usually access APIs using API keys, accounts, subscriptions, or prepaid credits.

x402 introduces a different model.

A service can respond to an HTTP request with:

```
http
HTTP/1.1 402 Payment Required
```
The response contains the payment requirements.

The agent can then:

Read the payment requirements.
Create and sign a payment payload using its wallet.
Retry the request with the payment signature.
Have the payment verified and settled.
Receive the requested resource.

This makes the payment process programmable and machine-to-machine, allowing an autonomous agent to pay for a service without requiring a human to manually complete a checkout flow.

The protocol uses HTTP 402 Payment Required to communicate payment requirements and allows the client to retry the request with a signed payment payload. Verification and settlement can be handled through an x402 facilitator.

### Tech Stack
AI & Orchestration
Python
Large Language Models
Multi-agent orchestration
Specialized research agents
Payments
x402 Protocol
USDC
EVM-compatible blockchain infrastructure
x402 Facilitator
Backend
Python
HTTP APIs
Modular service architecture
Frontend
Web-based research interface
