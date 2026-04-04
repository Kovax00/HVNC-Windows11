# HVNC-Windows11
PoC-HVNC windows 11 y windows 10 2026.

# HVNC Python - Hidden Virtual Desktop Control

<img width="1285" height="806" alt="image" src="https://github.com/user-attachments/assets/746fd0fd-5607-490a-a865-c1ffce98c4dc" />


## Descripción

Este proyecto implementa un sistema HVNC (Hidden Virtual Network Computing) en Python que permite crear, ejecutar y controlar un escritorio virtual oculto en sistemas Windows. A diferencia de soluciones tradicionales de acceso remoto, las aplicaciones se ejecutan en un contexto aislado que no es visible para el usuario local.

El sistema está compuesto por un cliente que opera sobre el host objetivo y un servidor que actúa como panel de control remoto.

---
# ATENCION🚩🚩
Este codigo solo es un POC, No usar de manera mal intencionada.

## Arquitectura

### Cliente

El cliente es responsable de:

- Crear un escritorio oculto mediante `CreateDesktopW`
- Ejecutar procesos dentro de ese contexto aislado
- Capturar el contenido gráfico del desktop virtual
- Codificar frames en formato JPEG
- Transmitir el stream al servidor vía TCP
- Recibir e inyectar eventos de entrada (mouse y teclado)

Componentes principales:

- Captura gráfica:
  - `PrintWindow`
  - `BitBlt`
  - Device Contexts (GDI)
- Inyección de eventos:
  - `PostMessageW`
  - `SendMessageW`
- Compatibilidad:
  - Aplicaciones Win32
  - Aplicaciones basadas en WinUI

---

### Servidor

El servidor proporciona:

- Listener TCP para conexiones entrantes
- Interfaz gráfica basada en `tkinter`
- Renderizado en tiempo real del stream recibido
- Envío de eventos de interacción remota
- Menú dinámico de aplicaciones detectadas

---

## Protocolo de Comunicación

### Cliente → Servidor

| Tipo       | Formato                          |
|------------|----------------------------------|
| Frame      | uint32 size + datos JPEG         |
| Handshake  | uint32 width + uint32 height + JSON |

---

### Servidor → Cliente

| Código | Acción         | Payload                         |
|--------|--------------|----------------------------------|
| 0x01   | Mouse move   | int32 x, int32 y                |
| 0x02   | Mouse click  | int32 x, int32 y, uint8 button  |
| 0x03   | Key event    | uint16 vk, uint8 flags          |
| 0x04   | Double click | int32 x, int32 y, uint8 button  |
| 0x05   | Launch app   | uint16 len + string UTF-8       |

---

## Técnicas Implementadas

### Desktop Aislado

- Uso de `CreateDesktopW` para generar un entorno independiente
- Ejecución de procesos dentro de `WinSta0\<desktop>`
- Separación completa del escritorio interactivo del usuario

---

### Captura de Pantalla

- Uso de `PrintWindow` para renderizar ventanas fuera de foco
- Composición manual del orden Z (Z-order)
- Extracción de bitmap mediante `GetDIBits`
- Conversión a imagen y compresión JPEG usando Pillow

---

### Inyección de Input

- Eventos enviados directamente a ventanas mediante mensajes Win32
- Traducción de coordenadas Screen → Client
- Manejo de:
  - `WM_MOUSEMOVE`, `WM_LBUTTONDOWN`, etc.
  - `WM_KEYDOWN`, `WM_KEYUP`
- Adaptación para entornos WinUI mediante top-level window routing

---

### Ejecución de Aplicaciones

Resolución de ejecutables mediante:

- Registro de Windows (`App Paths`)
- Paths comunes:
  - `%LOCALAPPDATA%`
  - `%PROGRAMFILES%`
- Aplicaciones UWP vía PowerShell (`Get-AppxPackage`)

Ejecución dentro del desktop oculto con `CreateProcessW`.

---

## Dependencias

Instalar:

```bash
pip install pillow
