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

## 3. Corregir o Reescribir el Último Commit (Amend)

Utiliza este flujo cuando hayas cometido un error en el mensaje de tu último commit o si olvidaste incluir cambios en algún archivo y no deseas generar un commit nuevo.

### Caso A: Cambiar solo el mensaje del último commit (sin abrir Vim)
Permite reescribir el texto de descripción directamente desde la terminal.
```bash
git commit --amend -m "tu nuevo mensaje corregido"
```

### Caso B: Añadir nuevos cambios al último commit (manteniendo el mismo mensaje)
Agrega modificaciones recientes al commit anterior sin alterar su descripción.
```bash
git add .
git commit --amend --no-edit
```

### Paso crucial: Actualizar GitHub si el commit ya se había subido
Si ya habías hecho `push` del commit original a GitHub, deberás forzar la actualización de manera segura.
```bash
git push --force-with-lease origin develop
```

---

## Resumen del Flujo Completo (Cheat Sheet Rápido)

| Objetivo | Comandos en orden |
| :--- | :--- |
| **Subir a develop** | `git status` <br> `git add .` <br> `git commit -m "mensaje"` <br> `git push origin develop` |
| **Pasar develop a main** | `git checkout main` <br> `git pull origin main` <br> `git merge develop` <br> `git push origin main` <br> `git checkout develop` |
| **Reescribir último commit** | `git add .` *(si hay cambios)* <br> `git commit --amend -m "nuevo mensaje"` <br> `git push --force-with-lease origin develop` |
| **Refrescar último commit** | `git add .` <br> `git commit --amend --no-edit` <br> `git push --force-with-lease origin develop` |
