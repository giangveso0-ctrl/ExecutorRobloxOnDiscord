# 🚀 RobloxOnDiscord — Remote WebSocket Executor & Debugger

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Roblox-Lua%20U-red.svg" alt="Roblox Lua">
  <img src="https://img.shields.io/badge/WebSocket-Port%208765-brightgreen.svg" alt="WebSocket Port">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 📌 Table of Contents / Mục Lục

1. [English Guide](#-english-guide)
   - [Overview](#overview)
   - [Repository Architecture](#repository-architecture)
   - [Prerequisites & Software Downloads](#prerequisites--software-downloads)
   - [Recommended Roblox Executors](#recommended-roblox-executors)
   - [Installation & Setup](#installation--setup)
   - [Slash Commands & Usage](#slash-commands--usage)
   - [Detailed Guide: /human Command](#detailed-guide-human-command)
2. [Hướng Dẫn Tiếng Việt](#-hướng-dẫn-tiếng-việt)
   - [Tổng Quan Dự Án](#tổng-quan-dự-án)
   - [Cấu Trúc Mã Nguồn](#cấu-trúc-mã-nguồn)
   - [Yêu Cầu Hệ Thống & Link Tải](#yêu-cầu-hệ-thống--link-tải)
   - [Danh Sách Executor Khuyên Dùng](#danh-sách-executor-khuyên-dùng)
   - [Cài Đặt & Vận Hành](#cài-đặt--vận-hành)
   - [Danh Sách Lệnh Discord](#danh-sách-lệnh-discord)
   - [Hướng Dẫn Chi Tiết Lệnh /human](#hướng-dẫn-chi-tiết-lệnh-human)
3. [Credits & Acknowledgments](#-credits--acknowledgments)
4. [Disclaimer](#-disclaimer)

---

# 🌐 English Guide

## Overview

**RobloxOnDiscord** is an advanced, high-performance bridge system that links a custom Python Discord Bot directly to a running Roblox game client (`RobloxPlayerBeta.exe`) using a local WebSocket server running on `ws://localhost:8765`. 

It enables developers, game testers, and exploit researchers to execute Lua code, load large script files remotely, toggle player features (ESP, Flight, Speed), and manipulate character physics in real time from a dedicated Discord channel (`#debug`).

---

## Repository Architecture

```text
├── bot.py         # Main Python script hosting Discord Bot & WebSocket server
├── bridge.lua     # Roblox Lua client script establishing local WebSocket bridge
└── start.bat      # Windows batch script for one-click startup
