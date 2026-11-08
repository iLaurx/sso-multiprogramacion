# Actividad 10: cambios y trabajo por equipo

**Materia:** Sistemas Operativos  
**Actividad:** Programa 5, planificación Round Robin

## De FCFS a Round Robin

La actividad 10 continúa el simulador que ya tenemos. El cambio principal es que los procesos compartirán la CPU por turnos usando Round Robin.

### ¿Qué es el quantum?

Es el tiempo máximo que un proceso puede usar la CPU en cada turno. Al iniciar, además de elegir cuántos procesos habrá, se pedirá el valor del quantum. Si al terminar su turno el proceso sigue pendiente, pasa al final de listos; cuando le toque otra vez, continúa desde donde quedó.

| Situación | Qué debe pasar |
| --- | --- |
| Termina antes o justo al vencer | El proceso pasa a terminados y se guarda su resultado. No vuelve a listos. |
| Se acaba el quantum | Si todavía falta trabajo, sale de CPU y se coloca al final de la cola de listos. |
| Se bloquea con E | Pasa a bloqueados durante 9 segundos simulados. Al volver, espera su turno en listos. |
| Sale por error con W | Pasa a terminados con ERROR y libera su espacio en memoria. |

**Ejemplo:** con quantum 3, P1 usa la CPU durante 3 segundos. Si todavía no termina, va al final de listos y entra el siguiente. Cuando P1 vuelva a usar la CPU, conserva los 3 segundos que ya ejecutó y comienza un nuevo turno.

### Qué se conserva

Los cinco estados, el máximo de 3 procesos en memoria, el reloj, la generación de procesos con N, la tabla con B, la pausa y los tiempos. Los controles siguen siendo E, W, P, C, N y B.

**Punto de partida:** se observan componentes de la actividad 8 en el motor, la API y el frontend; el archivo `estado.md` no refleja toda esa integración. Antes de implementar, el equipo debe comprobar la versión que va a usar. Este documento es un plan, no una certificación de pruebas.

## Team backend

La parte principal está en el motor: cambiar la forma de repartir los turnos y seguir registrando correctamente los tiempos de cada proceso.

### Qué tiene que hacer

- **Recibir y guardar el quantum** al crear la simulación. Propuesta: aceptar únicamente un número entero positivo. El PDF pide su valor, pero no define rango ni validación.
- **Contar el tiempo del turno actual.** Al vencer el quantum, regresar el proceso a listos si todavía no termina y dar la CPU al siguiente.
- **Reiniciar el contador del turno** cada vez que un proceso entra a CPU. Conservar por separado el tiempo total que ya ejecutó; la primera atención se registra una sola vez.
- **Mantener E, W y los bloqueos de 9 segundos.** Si se interrumpe o termina un proceso, cerrar su turno sin perder su avance. Los bloqueados siguen ocupando memoria.
- **Seguir admitiendo y creando procesos** con el límite de 3 residentes, sin alterar el orden de las colas ni el reloj.
- **Ampliar el estado que devuelve el motor** con el quantum elegido y el tiempo transcurrido del turno. Propuesta: usar `null` para este último cuando no haya proceso en CPU.

### Casos que debe probar

Quantum menor, igual y mayor al tiempo restante; un solo proceso; varias vueltas por CPU; interrupción, error y pausa a mitad de turno; CPU libre con bloqueados; creación de procesos; y conservación de los seis tiempos.

### Antes de entregar a API

Explicar el método de creación, los campos nuevos y ejemplos reales. Acordar un orden fijo cuando vencen el quantum y se desbloquea un proceso en el mismo segundo. El PDF no precisa esa prioridad: debe documentarse y probarse.

## Team API

La API recibirá el quantum y lo entregará junto con el estado del simulador. Puede seguir usando las rutas que ya existen.

### Qué tiene que hacer

- **Recibir el quantum al crear la simulación** junto con la cantidad inicial de procesos. Validar el valor acordado y pasar ambos datos al motor.
- **Devolver el quantum y el tiempo del turno** en las respuestas que usa la pantalla. Los valores y tiempos deben venir del motor; la API no debe llevar otro contador.
- **Mantener las acciones existentes:** interrupción, error, pausa, continuación y creación de procesos. Las teclas las interpreta la pantalla, no la API.
- **Conservar la coordinación con el reloj.** Crear, consultar y aplicar acciones deben seguir protegidos para que la pantalla reciba un estado consistente. Consultar no debe avanzar el tiempo.
- **Actualizar el contrato y los ejemplos** con una creación que incluya quantum, un cambio de turno, una pausa y una CPU libre.

### Casos que debe probar

Validar quantum ausente o inválido según el contrato que acuerden; comprobar que se conserva entre consultas; revisar cambios de turno con el reloj, pausa y continuación, E/W, N, errores y simulaciones independientes.

### Para entregar a frontend

Compartir los nombres finales de los campos, la ruta y el cuerpo de creación, las respuestas reales y las reglas de error. Una CPU libre con bloqueados sigue siendo una simulación activa.

**Decisión del equipo:** si el quantum será obligatorio o tendrá un valor predeterminado es una decisión de compatibilidad de la API. La interfaz debe pedirlo siempre, porque así lo indica la actividad.

## Team frontend

La pantalla debe permitir elegir el quantum y hacer visibles los turnos. Aprovecharemos la interfaz actual y sus controles.

### Qué tiene que hacer

- **Agregar el campo de quantum** junto a la cantidad inicial de procesos. Validar que el valor sea entero y positivo y enviarlo al iniciar.
- **Mostrar el quantum elegido y el tiempo transcurrido del turno** del proceso en CPU, además de su tiempo ejecutado total y su restante.
- **Hacer visible el avance de la cola de listos.** Mostrar los procesos en el orden recibido y reflejar cuando el que estaba en CPU pasa al final y entra el siguiente. Puede usarse un movimiento o una indicación clara del cambio.
- **Conservar E, W, P, C, N y B.** Actualizar textos e historial para que expliquen cuándo un proceso vuelve a listos porque agotó su turno. B pausa y muestra la tabla; C continúa.
- **Conservar la tabla de procesos** al consultarla y al finalizar, con estados, operaciones, resultados y tiempos. Distinguir ERROR y mostrar el tiempo restante de bloqueo cuando corresponda.
- **Tomar los valores del servidor.** El quantum y los tiempos se muestran según la respuesta de la API; la pantalla no debe llevar un contador independiente para decidir cambios de proceso.

## Revisión entre los tres equipos

Probar con quantum 1, con un proceso que termine justo al vencer, con varios procesos dando vueltas, con E/W/P/C/N/B y con la CPU libre por bloqueos. Revisar que el orden de la pantalla coincida con el servidor y que la tabla final quede visible.

**Reporte:** datos personales y de la materia, actividad, objetivo, lenguaje y estructuras usadas, y conclusiones.

Fuente de requisitos: Actividad 10 SSO.pdf, páginas 1 y 2. Este archivo reproduce el contenido del PDF de planificación de la actividad 10.
