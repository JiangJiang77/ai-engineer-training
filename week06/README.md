# 第 6 周 - DSL语言设计与执行引擎

本项目包含一系列用于学习 DSL语言设计与执行引擎 的 Jupyter notebook 文件。

## 开始使用

以下说明将帮助您在本地机器上设置和运行此项目，以便进行开发和学习。

### 环境要求

*   Python 3.11 或更高版本
*   已安装 [uv](https://github.com/astral-sh/uv)。`uv` 是一个极速的 Python 包安装工具。

### 安装步骤

1.  **安装依赖:**
    在项目根目录中打开终端，然后运行：
    ```bash
	cd week06
	pip install uv
    uv sync --locked
    ```
    这将自动安装依赖并在当前目录下创建一个名为 `.venv` 的虚拟环境目录。

2.  **激活虚拟环境:**
    *   在 macOS 和 Linux 上:
        ```bash
        source .venv/bin/activate
        ```
    *   在 Windows 上:
        ```bash
        .venv\Scripts\activate
        ```

## 设置项目专属的 Jupyter 内核

为了确保您的 notebook 使用本项目定义的特定 Python 环境和依赖项，您可以将其注册为自定义的 Jupyter 内核。

1.  **激活虚拟环境:**
    首先，请确保您已经激活了项目的虚拟环境。
    ```bash
    source .venv/bin/activate
    ```

2.  **注册内核:**
    运行以下命令，将当前环境注册为一个新的 Jupyter 内核：
    ```bash
    python -m ipykernel install --user --name=week06 --display-name="AI工程化(week06)"
    ```

	运行下面的命令查看当前的 kernel 列表：
	```bash
	jupyter kernelspec list
	```
	应该能看到类似下面的输出:
	```bash
	Available kernels:
	week06     /Users/your_username/Library/Jupyter/kernels/week06
	python3    /usr/local/share/jupyter/kernels/python3
	```
	如果看到 `week06` 在列表中，则说明注册成功。
	

## 运行 JupyterLab

安装完成后，您可以运行 JupyterLab。

1.  **启动 JupyterLab:**
    在您的终端中（确保虚拟环境仍处于激活状态），运行：
    ```bash
    jupyter lab
    ```
    这将启动 Jupyter 服务，并在您的默认网络浏览器中打开一个新标签页。

2.  **打开 Notebook 文件:**
    在浏览器标签页中，单击任何 `.ipynb` 文件以打开并运行它。

3.  **选择内核:**
    可以在 **Kernel > Change kernel** 菜单中看到并选择 **"AI工程化(week06)"**。这可以确保您的 notebook 在正确的项目环境中运行。

## 运行 Python 脚本示例

除了 Notebook 外，本项目还提供了一些可直接运行的 Python 脚本。

### 运行 p03-mcpVS.DSL.py

该脚本展示了如何使用 Python 处理退款逻辑以及对应的 DSL 描述。

```bash
# 确保已激活虚拟环境
python p03-mcpVS.DSL.py
```

### 运行 p05-interVS.exterl.py

该脚本展示了内部 DSL 和外部 DSL 的对比。

```bash
# 确保已激活虚拟环境
python p05-interVS.exterl.py
```

### 运行 p06-5个特征.py

该脚本列出了优秀 DSL 设计的 5 个关键特征及其对比示例。

```bash
# 确保已激活虚拟环境
python p06-5个特征.py
```

### 运行 p07-常见场景.py

该脚本展示了 DSL 在客服、风控、多 Agent 协作等领域的常见应用场景。

```bash
# 确保已激活虚拟环境
python p07-常见场景.py
```

### 运行 P19-纵深防御体系.py

该脚本由 `P19-纵深防御体系.ipynb` 提取而来，包含 4 个纵深防御组件示例：
- 输入清洗（`InputSanitizer`）
- Schema/角色权限限制（`SchemaRestrictor`）
- SQL 模板化（`SQLTemplater`）
- SQL 风险校验（`SQLValidator`）

```bash
# 确保已激活虚拟环境
python P19-纵深防御体系.py
```
