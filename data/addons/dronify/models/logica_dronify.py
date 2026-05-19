def calcular_consumo_vuelo(peso_total, distancia_total, riesgo_valor, es_vip=False):
    """
    NUEVA LÓGICA DE CONSUMO PARA RECUPERACIÓN:
    - Coste fijo despegue/aterrizaje: 5%
    - Coste por peso: 1.2% por cada kilo.
    - Coste por distancia: 0.5% por cada kilómetro.
    - Penalización por Riesgo: El consumo total se incrementa un 10% por cada nivel de riesgo.
    (Ejemplo: Riesgo 1 = +10%, Riesgo 5 = +50%).
    - Descuento VIP: Si el cliente es VIP, -10% al consumo final total.
    """

    # 1. Consumo base (Fijo + Peso + Distancia)
    consumo = 5.0 + (peso_total * 1.2) + (distancia_total * 0.5)

    # 2. Aplicar multiplicador de riesgo
    # Riesgo 1 -> 1.1 | Riesgo 5 -> 1.5
    multiplicador_riesgo = 1 + (riesgo_valor * 0.1)
    consumo = consumo * multiplicador_riesgo

    # 3. Aplicar reducción VIP sobre el total penalizado
    if es_vip:
        consumo = consumo * 0.9

    return round(consumo, 2)