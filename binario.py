from iqoptionapi.stable_api import IQ_Option
import asyncio
import time
import datetime
from collections import Counter

SOME_VOLUME_THRESHOLD = 1000  # Defina o valor que você considera adequado para o volume
SOME_PRICE_THRESHOLD = 0.0001  # Defina o valor que você considera adequado para a diferença de preço

async def main():
    email = "geloxa@gmail.com"  # Seu email da IQ Option
    password = "Olecramm2015*"  # Sua senha (altere para a senha correta)
    API = IQ_Option(email, password)
    API.connect()
    if API.check_connect():
        print("\nConectado com sucesso\n")
    else:
        print(f"\nHouve um problema na conexão: {API.get_last_error()}\n")
        return
    # Definir conta como DEMO por padrão
    API.change_balance("PRACTICE")
    print("Conta DEMO selecionada\n")
    user_info = API.get_profile_ansyc()
    name = user_info['name']
    balance = API.get_balance()

    print(f"Você está conectado à conta: {name}")
    print(f"Saldo atual: {balance:.2f}\n")
    asset_name = "EURUSD-OTC"  # Ativo padrão
    print(f"Ativo selecionado: {asset_name}\n")
    entry_value = 10  # Valor de entrada padrão
    martingale_count = 12  # Quantidade de martingales padrão
    stop_loss = 2000  # Valor de stop loss padrão
    stop_win = 3500  # Valor de stop win padrão
    print("Iniciando negociação...\n")
    
    while True:
        if balance <= stop_loss or balance >= stop_win:
            break
            
        candles = API.get_candles(asset_name, 60, 10, time.time())  # Obter os preços de fechamento dos últimos 10 minutos
        prices = [candle['close'] for candle in candles]
        volume = sum([candle['volume'] for candle in candles])
        
        avg_price = sum(prices) / len(prices)
        direction_counts = Counter(['put' if price > avg_price else 'call' for price in prices])
        direction = direction_counts.most_common(1)[0][0]
        
        if volume > SOME_VOLUME_THRESHOLD and max(prices) - min(prices) > SOME_PRICE_THRESHOLD:
            await perform_trade(API, asset_name, entry_value, martingale_count, stop_loss, stop_win, direction)
        else:
            await asyncio.sleep(1)  # Aguardar até que os requisitos sejam atendidos

async def perform_trade(API, asset_name, entry_value, martingale_count, stop_loss, stop_win, direction):
    martingale_attempts = 0
    while martingale_attempts <= martingale_count:
        current_time = datetime.datetime.now()
        if current_time.second >= 58:
            print(f"Realizando negociação '{direction}' (Tentativa {martingale_attempts + 1})...")
            check, order_id = API.buy(entry_value, asset_name, direction, 1)
            if check:
                print(f"Ordem '{direction}' aberta com entrada de {entry_value} em {asset_name}")
                print(f"ID da ordem: {order_id}\n")
                result = await check_win(API, order_id)
                if result == 'win':
                    print("Ordem encerrada com lucro!\n")
                    entry_value /= (1 + 0.15)
                    break
                elif result == 'loose':
                    print("Ordem encerrada com prejuízo. Aplicando Martingale...")
                    entry_value *= (1 + 0.15) * 2
                    if entry_value <= stop_loss:
                        martingale_attempts += 1
                        continue
                    else:
                        print("Limite de Martingale atingido. Encerrando operação.\n")
                        break
                else:
                    print("Ordem encerrada em break-even. Encerrando operação.\n")
                    break
            else:
                print("Erro ao abrir a ordem. Tentando novamente...\n")
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(1)

async def check_win(API, order_id):
    while True:
        result = API.check_win_v4(order_id)
        if result and isinstance(result, tuple) and len(result) > 0:
            result_value = result[0]
            return result_value
        else:
            print("Aguardando resultado da ordem...\n")
            await asyncio.sleep(1)
