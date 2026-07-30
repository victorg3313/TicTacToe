# TicTacToe
Este es una version del TicTacToe usando machine learning para mejorar el nivel de la ia contra la que se esta jugando ademas de tambien tener una version de 2 jugadores.

Características Principales

* **Estética Cyberpunk Neón:** Interfaz visual atractiva basada en Canvas con efectos visuales dinámicos, fuentes estilo consola y diseño responsivo de paneles oscuros.
* **IA con Machine Learning Real:** La computadora no utiliza reglas fijas ni un algoritmo minimax escrito a mano. Aprende a jugar desde cero mediante **Self-Play (auto-entrenamiento)** aplicando Aprendizaje por Refuerzo con Diferencia Temporal (TD-Learning).
* **Sistema de Dificultad Dinámico:** 
  * Los 5 niveles de dificultad están controlados por la tasa de exploración de la IA (*Epsilon-Greedy*), desde un modo novato hasta un juego prácticamente perfecto en el Nivel 5.
  * Si le ganas a la IA en modo solitario, automáticamente subes de nivel.
* **Efectos de Audio Retro:** Generación de efectos de sonido estilo 8-bits nativos (compatibles con Windows sin requerir archivos externos de audio).
* **Persistencia del Cerebro:** El modelo entrenado se guarda localmente en un archivo JSON (`ttt_brain.json`) para evitar reentrenar en cada inicio.
