from flask import Flask, render_template, request, jsonify
from app.models import CargoRequest
from app.api import SalesIntegrationLayer

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plan', methods=['POST'])
def plan():
    data = request.json
    cargos = []
    for idx, item in enumerate(data['cargos']):
        dims = []
        if item.get('length'):
            dims = [{"l": float(item['length']), "w": float(item['width']), "h": float(item['height'])}]
        cargos.append(CargoRequest(
            id=f"C-{idx+1}",
            destination=item['dest'],
            weight=float(item['weight']),
            volume=float(item['volume']),
            pieces=int(item['pieces']),
            dims=dims,
            shc=item.get('shc', []),
            assigned_uld_type=item.get('uld_type') if item.get('uld_type') != "AUTO" else None
        ))

    result = SalesIntegrationLayer.confirm_booking("TEST-FLIGHT", ["TPE", "LAX"], cargos)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)