import json
import textwrap
from app.models import CargoRequest, ForcedGroup # <--- 注意這裡要 import ForcedGroup
from app.planner.core_engine import CorePlanningEngine
from app.config import AircraftMap

def print_wrapped_row(pos, type_, dest, weight, uld_id, contents_str, content_width=60):
    wrapped_contents = textwrap.wrap(contents_str, width=content_width)
    first_line = wrapped_contents[0] if wrapped_contents else ""
    print(f"{pos:<5} | {type_:<8} | {dest:<4} | {weight:<8} | {uld_id:<8} | {first_line}")
    for line in wrapped_contents[1:]:
        print(f"{'':<5} | {'':<8} | {'':<4} | {'':<8} | {'':<8} | {line}")
    print("-" * 125)

if __name__ == "__main__":
    print("=== B747-400F Load Planner (With Forced Groups) ===\n")
    AircraftMap.initialize_maps()

    # === 測試資料 (原本那批) ===
    test_cargos = [
        # ... (這裡保留您原本的 test_cargos，為了節省版面我不重複貼，請保留原本的資料) ...
        # 如果您懶得複製，可以用下面這兩筆簡單的來測指定功能：
        CargoRequest(id="VIP-001", destination="LAX", weight=2000.0, volume=5.0, pieces=10),
        CargoRequest(id="VIP-002", destination="LAX", weight=3000.0, volume=8.0, pieces=15),
        CargoRequest(id="NORMAL-01", destination="LAX", weight=1000.0, volume=3.0, pieces=5),
    ]
    
    # === [關鍵測試] 指定合收功能 ===
    # 情境：User 強制要求 "VIP-001" 和 "VIP-002" 這兩票貨，
    # 必須合收，且只能用 1 個 Q6 (M) 盤。
    # (註：2000+3000=5000kg，還沒超重，應該裝得下)
    
    forced_rules = [
        ForcedGroup(
            group_id="VIP-BOX", 
            cargo_ids=["VIP-001", "VIP-002"], # 指定這兩票 ID 開頭的貨
            target_uld_type="M", 
            max_uld_count=1 # 只能用 1 個盤
        )
    ]
    
    engine = CorePlanningEngine(route=["TPE", "LAX"])
    
    print(f">>> 執行規劃 (含強制指定規則: {forced_rules[0].group_id})...")
    
    # 注意：這裡多傳了一個參數 forced_groups
    result = engine.plan_flight(test_cargos, forced_groups=forced_rules) 
    
    # ... (後面的 print 邏輯不變) ...
    # 這裡直接印出，看 VIP-001 和 VIP-002 是否被鎖在同一個 FRC-xxx 盤裡
    print("\n[ULD ALLOCATION]")
    print(f"{'POS':<5} | {'TYPE':<8} | {'DEST':<4} | {'WGT(KG)':<8} | {'ULD ID':<8} | {'CONTENTS'}")
    print("=" * 105)
    
    sorted_vis = sorted(result['visualization'], key=lambda x: str(x['pos']))
    for u in sorted_vis:
        contents_str = ", ".join(u.get('contents', []))
        print_wrapped_row(u['pos'], u['type'], u.get('dest','N/A'), u['weight'], u['uld'], contents_str, 80)

    # 檢查有沒有溢出 (Overflow)
    if result.get('action_required'):
        print("\n[!!! ACTION REQUIRED !!!]")
        for act in result['action_required']:
            print(f"Group: {act['group_id']}")
            print(f"Msg: {act['message']}")