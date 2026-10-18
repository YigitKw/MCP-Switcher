<div align="center">

[🇬🇧 English](README.md) | [🇹🇷 Türkçe](README.tr.md)

# MCP Switcher

**Gemini, Claude Desktop, Cursor, OpenCode ve Codex için sıfır bağımlılıklı, çapraz platform MCP profil yöneticisi.**

</div>

---

## Genel Bakış

**MCP Switcher**, Model Context Protocol (MCP) sunucu profillerini birden fazla yapay zeka istemcisi arasında yapılandıran ve profiller arası geçiş sağlayan bir komut satırı aracıdır.

Aktif araç şemalarının tamamının bağlam penceresine (context window) dahil edilmesi token tüketimini artırır ve çıkarım gecikmesini (inference latency) yükseltir. MCP Switcher, sunucu yapılandırmalarını görev odaklı profillere (`coding`, `research`, `academic` veya `minimal`) ayırarak istemcilere tek bir komutla uygulanmasını sağlar.

## Temel Özellikler

- **Çoklu İstemci Senkronizasyonu:** Gemini, Claude Desktop, Cursor, OpenCode ve Codex yapılandırma dosyalarını eşzamanlı olarak günceller.
- **Korumalı Birleştirme (Non-Destructive Merge):** Yalnızca `mcpServers` alanını günceller; editörlerde tanımlı özel kısayolları, temaları ve sistem ayarlarını muhafaza eder.
- **Çalışma Zamanı ve Servis Doğrulaması:** Komutların `PATH` üzerindeki varlığını denetler ve Docker tabanlı araçlar öncesinde Docker servisinin yanıt verebilirliğini teyit eder.
- **Otomatik Başlangıç Yapılandırması (Auto-Bootstrap):** İlk çalıştırmada sistemde kurulu istemcilerin mevcut araçlarını tarar ve varsayılan bir temel profil (`default`) oluşturur.
- **8 Yerleşik Dil:** İngilizce, Türkçe, İspanyolca, Çince, Rusça, Almanca, Fransızca ve Arapça.
- **Sıfır Dış Bağımlılık:** Tamamen standart Python kütüphaneleri kullanılarak geliştirilmiştir.

---

## Kurulum

### macOS & Linux (Terminal Betiği)
```bash
curl -fsSL https://raw.githubusercontent.com/YigitKw/MCP-Switcher/main/install.sh | bash
```
> Terminal üzerinden indirildiği için macOS tarayıcı karantinası özniteliği (`com.apple.quarantine`) eklenmeden doğrudan `~/.local/bin` dizinine kurulur.

### Windows (PowerShell Betiği)
```powershell
irm https://raw.githubusercontent.com/YigitKw/MCP-Switcher/main/install.ps1 | iex
```

### Evrensel Paket (pip / pipx)
```bash
pipx install mcp-switch
# veya
pip install mcp-switch
```

---

## Mimari ve Çalışma Mantığı

MCP Switcher, yapılandırılan tüm sunucu tanımlarını `~/.gemini/config/profiles/library.json` yolundaki ana kütüphanede saklar. Profiller bu tanımların alt kümelerini gruplandırır:

```
                  ┌───────────────────────────────┐
                  │      Merkezi Sunucu Havuzu    │
                  │  (GitHub, Postgres, Memory...)│
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────────────────┐          ┌──────────────────────────────┐
│  Profil: "coding"            │          │  Profil: "research"         │
│  - GitHub                    │          │  - Brave Search              │
│  - Postgres                  │          │  - Memory                    │
│  - Filesystem                │          │  - Sequential Thinking       │
└──────────────┬───────────────┘          └──────────────┬───────────────┘
               │ (mcp-switch coding)                     │
               ▼                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Senkronize İstemciler: Gemini, Claude Desktop, Cursor, OpenCode, Codex │
└────────────────────────────────────────────────────────────────────────┘
```

### Sunucu Yapılandırması ve Kimlik Doğrulama

Sunucu tanımları doğrudan dosya düzenlemesine gerek kalmadan eklenebilir:
1. **Etkileşimli Giriş:** `mcp-switch` çalıştırılıp `2. Yeni MCP Sunucusu Ekle` adımı seçilir. Arayüz; çalıştırılabilir komutu, argümanları ve gerekli ortam değişkenlerini (ör. `GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx`) adım adım kaydeder.
2. **JSON İçe Aktarma:** Yapay zeka modelleri tarafından üretilen ham yapılandırma blokları `JSON Yapıştır` seçeneğiyle doğrudan aktarılabilir.
3. **Kalıcı Depolama:** Profiller `~/.gemini/config/profiles/<profil_adi>.json` yolunda standart JSON dosyaları olarak saklanır.

---

## Kullanım

### Etkileşimli Arayüz
Etkileşimli terminal menüsünü başlatmak için argümansız çalıştırın:
```bash
mcp-switch
```

### Komut Satırı Kısayolları
```bash
mcp-switch <profil_adi>         # Belirtilen profili aktif eder (ör. mcp-switch coding)
mcp-switch status               # Aktif profili, istemcileri ve komut sağlık durumunu gösterir
mcp-switch list                 # Tanımlı tüm profilleri listeler
mcp-switch targets              # Senkronizasyona dahil edilecek istemcileri seçer
mcp-switch lang [tr|en|es|...]  # Görüntüleme dilini ayarlar
mcp-switch add                  # Yeni bir MCP sunucu tanımı ekler
mcp-switch edit                 # Profil oluşturur veya mevcut profilleri düzenler
```

## Lisans
MIT Lisansı. Açık kaynaklı ve ücretsizdir.
