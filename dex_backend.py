# Instalasi: Buka terminal dan ketik `pip install Flask requests gunicorn`
from flask import Flask, jsonify
import requests

# --- PENGATURAN DEX SCANNER ---
# ID Token di Solana.
# Anda bisa mendapatkan ID dari situs seperti Solscan.
TOKEN_MINT_ADDRESSES = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzL7GMYmCw54gK",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
}

# Pasangan yang ingin dipindai
PAIRS_TO_SCAN = [
    ("SOL", "USDC"),
    ("JUP", "USDC"),
    ("WIF", "SOL"),
    ("BONK", "SOL"),
]

# Jumlah input untuk simulasi harga (1 SOL, 1 JUP, dll.)
# Dihitung berdasarkan desimal token. 1 SOL = 10^9, 1 JUP = 10^6
INPUT_AMOUNTS = {
    "SOL": 1_000_000_000,
    "JUP": 1_000_000,
    "WIF": 1_000_000,
    "BONK": 100_000_000_000 # 100k BONK
}

# Inisialisasi aplikasi Flask
app = Flask(__name__)

def get_jupiter_price(input_symbol, output_symbol):
    """
    Mengambil harga dari Jupiter API untuk satu pasangan token.
    """
    input_mint = TOKEN_MINT_ADDRESSES.get(input_symbol)
    output_mint = TOKEN_MINT_ADDRESSES.get(output_symbol)
    amount = INPUT_AMOUNTS.get(input_symbol)

    if not all([input_mint, output_mint, amount]):
        return None

    api_url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps=50"
    
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"Error fetching data from Jupiter API: Status {response.status_code}")
            return None
        
        data = response.json()
        
        # Sederhanakan kalkulasi harga untuk demonstrasi
        in_amount = int(data['inAmount'])
        out_amount = int(data['outAmount'])
        
        # Kalkulasi ini memerlukan info desimal yang akurat, untuk sekarang kita buat pendekatan
        # Ini tidak akan 100% akurat tanpa info desimal token output, tapi cukup untuk demo
        price = out_amount / in_amount if in_amount > 0 else 0

        # Kita gunakan pendekatan sederhana untuk mendapatkan harga
        # Harga riil = jumlah keluar / jumlah masuk, disesuaikan dengan desimal
        # Mari kita asumsikan harga per unit untuk kemudahan
        price_str = f"{price * (10**(9-6)):.6f}" # Contoh kasar untuk SOL/USDC

        return {
            "pair": f"{input_symbol}/{output_symbol}",
            "price": price_str,
            "route": data.get('marketInfos', [{}])[0].get('label', 'N/A')
        }
    except Exception as e:
        print(f"Error processing {input_symbol}/{output_symbol}: {e}")
        return None

# Membuat API endpoint '/dex-prices'
@app.route('/dex-prices', methods=['GET'])
def get_dex_prices():
    """
    Endpoint ini akan dipanggil oleh aplikasi React Native.
    """
    all_prices = []
    print("Menerima request dari aplikasi mobile...")
    for input_sym, output_sym in PAIRS_TO_SCAN:
        price_info = get_jupiter_price(input_sym, output_sym)
        if price_info:
            all_prices.append(price_info)
    
    print(f"Mengirim {len(all_prices)} harga DEX ke aplikasi.")
    # Mengembalikan data dalam format JSON
    return jsonify(all_prices)

@app.route('/', methods=['GET'])
def index():
    return "DEX Scanner Backend is running."

# Menjalankan server
if __name__ == '__main__':
    # Jalankan server
    # Gunicorn akan menangani host dan port saat di-deploy
    app.run()

