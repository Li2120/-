import os
import cv2
import numpy as np
import requests
import base64

# ==================== ⚙️ 配置区域 ====================
# 本地 iopaint 服务地址（端口默认 8080）
LAMA_API_URL = "http://localhost:8080/api/v1/inpaint"
# ====================================================

# 全局变量
drawing = False
ix, iy = -1, -1
fx, fy = -1, -1
roi_box_orig = None
scale_factor = 1.0
img_clone = None
temp_img_disp = None

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, fx, fy, drawing, img_clone, temp_img_disp, roi_box_orig, scale_factor
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        fx, fy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            fx, fy = x, y
            img_clone = temp_img_disp.copy()
            cv2.rectangle(img_clone, (ix, iy), (fx, fy), (0, 255, 0), 2)
            cv2.imshow("9:16 Local AI Box", img_clone)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        fx, fy = x, y
        cv2.rectangle(img_clone, (ix, iy), (fx, fy), (0, 255, 0), 2)
        cv2.imshow("9:16 Local AI Box", img_clone)
        
        x1, x2 = min(ix, fx), max(ix, fx)
        y1, y2 = min(iy, fy), max(iy, fy)
        
        if x2 - x1 > 3 and y2 - y1 > 3:
            orig_x1 = int(x1 / scale_factor)
            orig_y1 = int(y1 / scale_factor)
            orig_x2 = int(x2 / scale_factor)
            orig_y2 = int(y2 / scale_factor)
            roi_box_orig = (orig_x1, orig_y1, orig_x2, orig_y2)
            print(f"✅ 已成功框选原图区域: X[{orig_x1}~{orig_x2}], Y[{orig_y1}~{orig_y2}]")

def process_image_with_local_ai(img, box):
    height, width = img.shape[:2]
    x1, y1, x2, y2 = box
    
    x1 = max(0, min(x1, width))
    x2 = max(0, min(x2, width))
    y1 = max(0, min(y1, height))
    y2 = max(0, min(y2, height))
    
    # 构造标准单通道掩膜 (黑白图：水印区域为白色255，其余为黑色0)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[y1:y2, x1:x2] = 255
    
    try:
        # 编码为 JPG / PNG 并转换为 Base64 字符串
        _, img_encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 100])
        _, mask_encoded = cv2.imencode('.png', mask)
        
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')
        mask_base64 = base64.b64encode(mask_encoded).decode('utf-8')
        
        payload = {
            "image": f"data:image/jpeg;base64,{img_base64}",
            "mask": f"data:image/png;base64,{mask_base64}",
            "ldm_steps": 25
        }
        
        print("⏳ 正在调用本地 AI 大模型 (LaMa) 渲染中...")
        response = requests.post(LAMA_API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            arr = np.frombuffer(response.content, np.uint8)
            result_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if result_img is not None:
                print("✅ 本地 AI 渲染成功！")
                return result_img
        
        print(f"⚠️ 本地 AI 服务返回错误状态码: {response.status_code}, 响应: {response.text[:100]}...")
    except Exception as e:
        print(f"⚠️ 无法连接到本地 AI 服务 ({LAMA_API_URL}): {e}")
        
    # 如果连接或渲染失败，平滑降级至纯净本地算法
    print("🔄 自动降级使用纯净本地无痕算法...")
    mask_simple = np.zeros((height, width), dtype=np.uint8)
    mask_simple[y1:y2, x1:x2] = 255
    return cv2.inpaint(img, mask_simple, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

def main():
    global temp_img_disp, img_clone, scale_factor, roi_box_orig
    
    input_dir = "./input_images"
    output_dir = "./output_images"
    
    if not os.path.exists(input_dir) or not os.path.exists(output_dir):
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    if not files:
        print(f"'{input_dir}' 文件夹下没有找到图片。")
        return

    first_img_path = os.path.join(input_dir, files[0])
    orig_img = cv2.imdecode(np.fromfile(first_img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    
    if orig_img is None:
        print(f"无法读取图片: {first_img_path}")
        return

    h_orig, w_orig = orig_img.shape[:2]

    target_h = 820
    scale_factor = target_h / h_orig
    
    disp_w = int(w_orig * scale_factor)
    disp_h = int(h_orig * scale_factor)
    
    temp_img_disp = cv2.resize(orig_img, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
    img_clone = temp_img_disp.copy()

    win_name_1 = "9:16 Local AI Box"
    print("\n==========================================")
    print(f"💡 【步骤 1/2】本地 AI 模式：请在弹出的窗口中用鼠标框选水印")
    print("1. 框选好后，按 【回车键 (Enter)】 生成 AI 预览。")
    print("2. 按 【R键】 可以重新画框。")
    print("3. 按 【ESC键】 或点击窗口【X】直接退出程序。")
    print("==========================================\n")

    cv2.namedWindow(win_name_1, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name_1, disp_w, disp_h)
    cv2.setMouseCallback(win_name_1, draw_rectangle)

    while True:
        cv2.imshow(win_name_1, img_clone)
        key = cv2.waitKey(1) & 0xFF
        
        try:
            if cv2.getWindowProperty(win_name_1, cv2.WND_PROP_VISIBLE) < 1:
                cv2.destroyAllWindows()
                print("❌ 检测到窗口被关闭，程序已退出。")
                return
        except:
            pass

        if key == 27:
            cv2.destroyAllWindows()
            print("❌ 已按 ESC 键退出程序。")
            return
        elif key == 13:
            if roi_box_orig is not None:
                break
            else:
                print("⚠️ 请先用鼠标在图上画出一个方框！")
        elif key == ord('r') or key == ord('R'):
            img_clone = temp_img_disp.copy()
            roi_box_orig = None
            print("🔄 已重置，请重新画框。")
            
    cv2.destroyAllWindows()

    # --- 预览阶段 ---
    print("\n正在生成本地 AI 预览效果...")
    preview_img = process_image_with_local_ai(orig_img, roi_box_orig)
    preview_disp = cv2.resize(preview_img, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
    
    win_name_2 = "Preview Result - Press Y to Continue / N to Cancel"
    print("\n==========================================")
    print("💡 【步骤 2/2】AI 预览已生成！")
    print("1. 请查看弹出的预览窗口，确认去水印效果是否完美。")
    print("2. 按 【Y键】 或 【回车键】 确认满意，开始批量处理所有图片。")
    print("3. 按 【N键】、点击【X】或【ESC键】放弃并退出。")
    print("==========================================\n")

    cv2.namedWindow(win_name_2, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name_2, disp_w, disp_h)

    confirmed = False
    while True:
        cv2.imshow(win_name_2, preview_disp)
        key = cv2.waitKey(1) & 0xFF
        
        try:
            if cv2.getWindowProperty(win_name_2, cv2.WND_PROP_VISIBLE) < 1:
                confirmed = False
                print("❌ 检测到预览窗口被关闭，已取消。")
                break
        except:
            pass

        if key == 27:
            confirmed = False
            break
        elif key == 13 or key == ord('y') or key == ord('Y'):
            confirmed = True
            break
        elif key == ord('n') or key == ord('N'):
            confirmed = False
            break

    cv2.destroyAllWindows()

    if not confirmed:
        print("❌ 已取消批量处理。")
        return

    # 批量应用到所有图片
    print(f"\n✅ 确认通过，开始批量处理 {len(files)} 张图片...")
    for filename in files:
        in_path = os.path.join(input_dir, filename)
        img = cv2.imdecode(np.fromfile(in_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
            
        h_curr, w_curr = img.shape[:2]
        if h_orig == h_curr and w_orig == w_curr:
            curr_box = roi_box_orig
        else:
            rx1, ry1, rx2, ry2 = roi_box_orig
            curr_box = (
                int(rx1 * (w_curr / w_orig)),
                int(ry1 * (h_curr / h_orig)),
                int(rx2 * (w_curr / w_orig)),
                int(ry2 * (h_curr / h_orig))
            )
            
        cleaned_img = process_image_with_local_ai(img, curr_box)
        out_path = os.path.join(output_dir, "clean_" + filename)
        cv2.imencode('.jpg', cleaned_img)[1].tofile(out_path)
        print(f"✅ 已成功处理: {filename}")

    print("\n🎉 所有图片处理完毕！快去 'output_images' 文件夹查看结果吧。")

if __name__ == "__main__":
    main()