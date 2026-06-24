# Guía de Comandos Git: Guardar, Subir y Fusionar Cambios

Esta guía contiene los comandos de Git esenciales para gestionar el flujo de trabajo de este proyecto, desde guardar tus avances del día hasta fusionar tu rama de desarrollo (`develop`) con la rama principal (`main`).

---

## 1. Guardar y Subir Cambios en tu Rama de Trabajo (`develop`)

Utiliza este flujo cuando termines de hacer cambios cotidianos o pruebas en tu código y quieras respaldarlos en GitHub.

### Paso 1: Ver el estado de tus archivos
Permite ver qué archivos han sido modificados o agregados.
```bash
git status
```

### Paso 2: Preparar los cambios
Añade todos los archivos modificados y nuevos al área de preparación (stage).
```bash
git add .
```
*(Si solo quieres agregar un archivo específico, usa: `git add ruta/al/archivo.py`)*

### Paso 3: Confirmar los cambios (Commit)
Guarda tus cambios localmente con un mensaje descriptivo de lo que hiciste.
```bash
git commit -m "pruebas del dia 23"
```

### Paso 4: Subir los cambios a GitHub
Envía tu rama local `develop` y su historial al repositorio remoto.
```bash
git push origin develop
```

---

## 2. Fusionar `develop` en la Rama Principal (`main`)

Utiliza este flujo cuando la rama `develop` ya esté testeada, funcione correctamente y desees pasar esos cambios a producción (`main`).

### Paso 1: Cambiar a la rama `main`
Sal de la rama de desarrollo y muévete a la rama principal.
```bash
git checkout main
```

### Paso 2: Actualizar `main` local (Buena Práctica)
Trae los últimos cambios de GitHub por si acaso hubo modificaciones remotas.
```bash
git pull origin main
```

### Paso 3: Fusionar `develop` dentro de `main`
Trae todo el historial y cambios de `develop` a `main`.
```bash
git merge develop
```

### Paso 4: Subir la rama `main` actualizada a GitHub
Publica la fusión en tu repositorio remoto.
```bash
git push origin main
```

### Paso 5: Regresar a tu rama de desarrollo
Vuelve a la rama `develop` para continuar escribiendo código sin afectar a `main`.
```bash
git checkout develop
```

---

## Resumen del Flujo Completo (Cheat Sheet Rápido)

| Objetivo | Comandos en orden |
| :--- | :--- |
| **Subir a develop** | `git status` <br> `git add .` <br> `git commit -m "mensaje"` <br> `git push origin develop` |
| **Pasar develop a main** | `git checkout main` <br> `git pull origin main` <br> `git merge develop` <br> `git push origin main` <br> `git checkout develop` |
