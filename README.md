# -
用于ai生成的图片进行一个去水印；还在测试阶段，目前自用没问题

🛠️ 第一步：在新电脑上安装 Python 与依赖库确保新电脑上已经安装了 Python（建议 Python 3.10 或 3.12）。打开新电脑的终端（CMD 或 PowerShell），执行以下命令安装脚本所需的依赖库（包括 OpenCV、Requests 和 AI 服务端 IOPaint）：Bashpip install opencv-python numpy requests iopaint
📂 第二步：整理文件目录结构把你的 Python 脚本（例如命名为 interactive_remove.py）放进一个专门的文件夹中，并在该文件夹下创建两个子文件夹：input_images：把你要去水印的原始 9:16 图片放入此文件夹。output_images：用于存放处理好的干净图片（程序会自动生成，也可以提前建好）。当前目录结构看起来应该是这样的：Plaintext📁 你的工作文件夹/
 ┣ 📜 interactive_remove.py  (你发过去的代码文件)
 ┣ 📁 input_images/          (放入待处理的图片)
 ┗ 📁 output_images/         (处理后的图片会存放在这)
▶️ 第三步：启动本地 AI 服务因为这个脚本需要调用本地运行的 AI 大模型，每次使用前必须先启动后台服务：在新电脑上打开一个终端窗口。输入以下命令启动 AI 模型（第一次运行会自动下载 LaMa 模型文件，请保持网络畅通）：Bashiopaint start --model=lama --device=cpu --port=8080
看到提示 Application startup complete 或 Running on http://localhost:8080 后，请让这个黑窗口保持开启，不要关闭。  🚀 第四步：运行脚本处理图片新开第二个终端窗口。切换到你的代码所在文件夹路径：Bashcd 你的文件夹绝对路径
运行你的 Python 脚本：Bashpython interactive_remove.py
按照屏幕提示，在弹出的窗口中用鼠标框选水印，按 回车键 生成预览，确认无误后按 Y键，脚本就会自动把 input_images 里的图片全部批量处理并存入 output_images 文件夹中。  
