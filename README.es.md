<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/brand/hero-dark.png">
  <img src="docs/brand/hero-light.png" width="1280" alt="Local AI Workcell. Envía cada trabajo de documentos a un worker capaz de hacerlo y conserva prueba de cada traspaso. Para operadores que necesitan saber dónde está cada trabajo de IA y si pueden confiar en el resultado. Diagrama: una entrada ficticia entra a una celda local con borde amarillo, pasa por coordinator, ocr-node, validation-node y results-node, y sale como resultado verificado. Cada estación registra un hash en un riel de evidencia. Un ciclo punteado de ocr-node de vuelta al coordinator muestra los estados de recuperación WAITING_WORKER y RETRY_PENDING.">
</picture>

**[Abrir el recorrido en vivo](https://leonelivancortesrodriguez.github.io/local-ai-workcell/)** · [Ejecutarlo localmente](#ejecutarlo-localmente) · [Prueba de procesos v0.2](docs/V2_PROOF.md) (en inglés) · [English](README.md)

[![Verify synthetic Workcell](https://github.com/LeonelIvanCortesRodriguez/local-ai-workcell/actions/workflows/verify.yml/badge.svg)](https://github.com/LeonelIvanCortesRodriguez/local-ai-workcell/actions/workflows/verify.yml)

Un sistema local pequeño que envía cada trabajo de documentos a un worker capaz de hacerlo, registra cada traspaso y se recupera cuando un worker se cae. Es una prueba pública y sintética: una sola computadora, entradas ficticias y pruebas que cualquiera puede volver a correr.

La página de estado y la documentación técnica están en inglés.

## El problema

Cuando el trabajo de IA se reparte entre workers con distintas capacidades (uno hace OCR, otro valida, otro entrega), los trabajos se pierden entre ellos. El operador no puede decir con facilidad dónde está un trabajo, si terminó, qué lo cambió o cómo reanudarlo. Un resultado sin un registro confiable de sus traspasos es difícil de creer. Este repositorio muestra ese patrón de control en una sola computadora.

## Cómo se recupera

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="docs/brand/replay-poster.png">
  <img src="docs/brand/replay.gif" width="960" alt="Repetición del trabajo sintético 480a7caaea1a, un cuadro por evento registrado: NEW en el coordinator, WAITING_WORKER porque no hay worker de OCR disponible, ROUTED a ocr-node, RETRY_PENDING tras una falla transitoria simulada, ROUTED otra vez, OCR_DONE, VALIDATED en validation-node y DELIVERED en results-node.">
</picture>

Un trabajo de los datos de prueba incluidos, repetido desde su manifiesto: espera a un worker de OCR que falta sin gastar un intento, falla una vez, se vuelve a enrutar y se entrega en su segundo y último intento. El otro trabajo pasa directo. [Versión MP4](docs/brand/replay.mp4).

## Cómo funciona el flujo

1. **Entrada controlada.** Solo se admiten datos de prueba ficticios: dos SVG para v0.1 y tres PNG para v0.2. El ID del trabajo se deriva de los bytes de entrada y de la versión del pipeline, así que un envío duplicado devuelve el trabajo existente.
2. **Coordinator.** Enruta por etiqueta de capacidad (`ocr-node`, `validation-node`, `results-node`), nunca por nombre de equipo. En este demo, el coordinator y todos los workers comparten un solo proceso de Python.
3. **OCR.** v0.1 usa un simulador que lee los nodos de texto del SVG; no reconoce píxeles. v0.2 llama a Tesseract desde procesos de worker separados.
4. **Validación.** Guarda los hashes de origen, los conteos derivados y una marca obligatoria de revisión manual en campos separados. El OCR simulado no dice nada sobre precisión, así que la revisión manual sigue siendo obligatoria.
5. **Resultado verificado.** Se entrega una sola vez, con checksum del resultado.
6. **Recuperación.** Si falta un worker, el trabajo pasa a `WAITING_WORKER` y conserva su lugar sin gastar un intento. Una falla transitoria lo mueve a `RETRY_PENDING`; el segundo intento termina en éxito o en `FAILED`.

Cada estación registra un hash en el manifiesto. Los eventos de estado van depurados: guardan estado, fase, etiqueta genérica del worker y código de motivo, pero ningún texto del documento ni ruta local. Consulta el [mapa de arquitectura y estados](docs/ARCHITECTURE.md).

## Resultado y evidencia

| Estado | Qué cubre | Dónde verificarlo |
| --- | --- | --- |
| Implementado y probado | v0.1: IDs deterministas, enrutamiento por capacidad, cambios de estado válidos, espera, reintento acotado, protección contra duplicados, checksums, entrega | `python -m unittest`, [`tests/test_workcell.py`](tests/test_workcell.py) |
| Implementado y probado | v0.2: tres procesos de worker locales, registro autenticado por loopback, rechazo de una clave inválida, cola SQLite persistente, recuperación tras reinicio, una desconexión deliberada, Tesseract sobre tres imágenes fijas | pruebas con `WORKCELL_V2_INTEGRATION=1`, [`tests/test_v2.py`](tests/test_v2.py) |
| Observado una vez | 3 de 3 PNG entregados, 1 conexión interrumpida recuperada, 2 asignaciones de OCR simultáneas, 1030 ms en total (Python 3.14.5, Tesseract 5.5.0, 2026-10-26). Fue una sola corrida, no un benchmark | [`docs/v2-sample-report.json`](docs/v2-sample-report.json) |
| Reportado por el autor, sin verificar aquí | Leonel reporta usar un patrón similar en trabajo privado que abarca más de una computadora. Nada en este repositorio lo muestra, lo ejecuta ni lo prueba | Sin evidencia pública |
| Planeado | Transporte para workers remotos, particiones de red reales, conjuntos de OCR más amplios, control de competencia por GPU | [Berth](https://github.com/T-Crypt/berth) es solo una candidata con fuente revisada |

Una prueba de mutación altera un resultado entregado de v0.1 y exige que la verificación de checksum lo rechace.

## Vistas del producto

<img src="docs/brand/view-trail.png" width="1240" alt="Captura anotada de la tarjeta del trabajo 480a7caaea1ae818 con su rastro de ocho eventos abierto. Notas: el trabajo recuperado aparece abierto por defecto y con borde más grueso; la espera es un contorno punteado con reloj, el reintento una flecha circular y la entrega un cuadrado lleno; cada línea se lee del manifiesto.">

<img src="docs/brand/view-v2.png" width="1240" alt="Captura anotada de la sección v0.2: envío, cola persistente, dos procesos de worker de OCR, una conexión caída que se vuelve a encolar, y después validación y entrega, junto a un recuadro de observación que dice 3 de 3 entregados. Las notas explican los workers de Tesseract, la desconexión reencolada y que el tiempo medido es de una sola corrida local.">

<img src="docs/brand/view-mobile.png" width="940" alt="Captura anotada de la página de estado a 390 píxeles de ancho: la promesa, el conteo de entregados y los dos botones de acción caben en la primera pantalla, y el diagrama de ruta se vuelve vertical debajo de ellos.">

## El papel de Leonel y sus decisiones

**Problema elegido.** Mostrar, en una sola computadora y con entradas ficticias, cómo un coordinador puede enrutar trabajos de documentos por capacidad y conservar un registro verificable de cada traspaso y cada recuperación.

**Papel.** Leonel tomó las decisiones de operación, definió el alcance de la prueba pública y los datos ficticios, eligió los casos de falla y escribió las verificaciones de aceptación. Agentes de programación ayudaron a implementar el código, la página de estado y las pruebas.

**Decisiones que le dan forma al sistema**

- *Enrutar por capacidad, no por equipo.* Los workers se nombran por lo que pueden hacer (`ocr-node`, `validation-node`, `results-node`), así que la ruta de un trabajo depende de la capacidad que necesita. Los workers remotos están planeados, no construidos.
- *Esperar no es fallar.* Un worker faltante no cuesta un intento; el trabajo conserva su lugar.
- *Reintento acotado.* Dos intentos de OCR y después `FAILED`, para que nada se cicle.
- *Hash en cada traspaso.* Los hashes de entrada, OCR, resultado y entrega permiten detectar un resultado alterado.
- *Revisión manual activa.* El resultado dice cuándo su evidencia no alcanza para afirmar precisión.

**Restricciones.** Público y reproducible; sin documentos privados, nombres de equipos, credenciales ni logs; solo la biblioteca estándar de Python en tiempo de ejecución; ningún servicio de pago.

**Resultados observados.** Las 16 pruebas pasan con la integración activada. La corrida de ejemplo de v0.2 entregó 3 de 3 PNG ficticios y se recuperó de la desconexión deliberada.

**Tecnologías.** Python 3.11 a 3.14 (biblioteca estándar), SQLite, `multiprocessing.connection` con loopback autenticado, Tesseract (opcional, no incluido), GitHub Actions y una página de estado HTML estática generada.

## Limitaciones

Una computadora. Entradas ficticias. Sin nodo remoto, TLS, consenso distribuido, almacén de credenciales de producción, carga arbitraria de archivos ni documentos privados. La desconexión es deliberada y local; no demuestra recuperación ante una partición de red real. Nada aquí establece precisión general de OCR, confiabilidad entre varias computadoras, seguridad de producción ni resultados operativos. El análisis de privacidad es un detector acotado, así que el paquete público sigue necesitando revisión humana.

## Ejecutarlo localmente

El recorrido de v0.1 solo necesita Python 3.11 o más reciente.

```bash
python -m workcell.cli demo --output out
python -m workcell.cli verify --output out
```

Abre `out/index.html`. El directorio de salida debe no existir o estar vacío. El [`index.html`](index.html) incluido es la misma corrida sintética; actualízalo con `python scripts/refresh_demo.py`.

Para v0.2, instala Tesseract desde su paquete oficial y luego:

```bash
python -m workcell.v2 demo --output out-v2
```

Imprime las observaciones de entrega, interrupción, recuperación, asignaciones concurrentes y tiempo; escribe `out-v2/report.json` y deja `out-v2/queue.sqlite3` para inspección. Consulta [prueba y límites de v0.2](docs/V2_PROOF.md).

### Verificar

```bash
python -m unittest discover -s tests -v      # set WORKCELL_V2_INTEGRATION=1 for socket and OCR tests
python tests/mutation_check.py
python scripts/privacy_scan.py
python scripts/contrast_check.py
python scripts/package.py --output release
```

El [workflow](.github/workflows/verify.yml) corre todo esto en Python 3.11 a 3.14, regenera la página de estado, ejecuta ambos demos y construye el paquete dos veces para confirmar que es determinista. La insignia muestra el estado real del CI en GitHub; que pase localmente no significa que pase en CI. El [procedimiento de publicación](docs/RELEASE.md) cubre la etiqueta `v0.2.0`, el ZIP, el inventario y la reversión.

## Privacidad, recursos y licencia

Cada SVG y PNG de prueba es ficticio y se hizo para este repositorio. No se incluye ningún documento privado, identidad real de nodo, credencial, log operativo ni captura de pantalla personal. Lee [SECURITY.md](SECURITY.md).

Las imágenes del README y de redes se generan con el mismo código de diagramas que la página de estado (`python design/compose.py` y luego `node design/render.mjs`; consulta [design/README.md](design/README.md)). El código, la documentación, los datos de prueba y las imágenes del autor están bajo la [Licencia MIT](LICENSE). Archivo y Martian Mono se incluyen bajo la SIL Open Font License; consulta los [avisos de terceros](THIRD_PARTY_NOTICES.md).
