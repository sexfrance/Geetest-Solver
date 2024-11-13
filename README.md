<div align="center">
 
  <h2 align="center">Geetest v4 CAPTCHA Solver</h2>
  <p align="center">
A request based Python solution for solving Geetest v4 CAPTCHA challenges efficiently. The script provides both synchronous and asynchronous options to handle the challenges, with an API interface for integration.
    <br />
    <br />
    <a href="https://discord.cyberious.xyz">💬 Discord</a>
    ·
    <a href="https://github.com/sexfrance/Geetest-Solver#-changelog">📜 ChangeLog</a>
    ·
    <a href="https://github.com/sexfrance/Geetest-Solver/issues">⚠️ Report Bug</a>
    ·
    <a href="https://github.com/sexfrance/Geetest-Solver/issues">💡 Request Feature</a>
  </p>
</div>

### ⚙️ Installation

- Requires: `Python 3.8+`
- Set up a virtual environment:
  ```bash
  python3 -m venv venv
  ```
- Activate the virtual environment:
  - Windows: `venv\Scripts\activate`
  - macOS/Linux: `source venv/bin/activate`
- Install required packages:
  ```bash
  pip install -r requirements.txt
  ```
- Install Chromium for `patchright`:
  ```bash
  patchright install chromium
  ```
- Start:
  - Remove comments in the async and sync solver files for testing purposes and execute the respective scripts.

---

### 🔥 Features

- **API Server**: An API server built with FastAPI, allowing external integration to solve Geetest challenges.
- **Async and Sync Modes**: Provides both asynchronous and synchronous solvers for flexibility.
- **Detailed Logging**: Uses logmagix for detailed logs, aiding troubleshooting and progress tracking.
- **Efficient CAPTCHA Interaction**: Dynamically interacts with CAPTCHA elements and retrieves solutions with configurable retries.
- **Error Handling**: Comprehensive error reporting, with detailed status feedback for straightforward integration.

---

#### 📹 Preview

![Preview](https://i.imgur.com/bFP24ch.gif)

---

### 🚀 Usage

#### API Usage

The API provides a straightforward way to integrate the solver into web applications or automation scripts. By running the API server, you can solve Geetest CAPTCHAs on demand and retrieve results programmatically.

1. **Starting the API Server**

   To start the API server, use the following command in your terminal:

   ```bash
   uvicorn api_solver:app --reload --host 0.0.0.0 --port 8000
   ```

   - **Host**: `0.0.0.0` allows access from any network interface.
   - **Port**: The server runs on port `8000` by default, accessible at `http://localhost:8000`.

   With `--reload`, the server automatically restarts on code changes, useful for development.

2. **Creating a CAPTCHA Solve Task**

   After starting the server, you can create a CAPTCHA solve task by making a `POST` request to `/task/create`. This request initiates the CAPTCHA-solving process.

   **Example Request**:

   ```bash
   curl -X POST "http://localhost:8000/task/create" \
   -H "Content-Type: application/json" \
   -d '{"sitekey": "YOUR_SITEKEY", "url": "https://example.com"}'
   ```

   - **sitekey** (required): The sitekey specific to the CAPTCHA you want to solve.
   - **url** (optional): The URL of the page with the CAPTCHA. While not always necessary, providing the URL can improve solver performance.

   **Example Response**:

   ```json
   {
     "taskId": "abc12345-def6-7890-gh12-ijk345lmn678",
     "status": "processing"
   }
   ```

   - `taskId`: A unique identifier for your task.
   - `status`: Indicates that the task is currently being processed.

3. **Checking Task Status**

   After creating a task, you can periodically check its status to see if the CAPTCHA has been solved.

   **Example Request**:

   ```bash
   curl "http://localhost:8000/task/abc12345-def6-7890-gh12-ijk345lmn678"
   ```

   **Example Response**:

   - **Success**:
     ```json
     {
       "status": "ready",
       "solution": {
         "response": "CAPTCHA_RESPONSE",
         "elapsed": 3.57
       },
       "error": null
     }
     ```
     - `response`: The CAPTCHA solution token.
     - `elapsed`: Time in seconds taken to solve the CAPTCHA.
   - **Failure**:
     ```json
     {
       "status": "failed",
       "solution": null,
       "error": "Captcha challenge failed."
     }
     ```
     - `status`: `failed` indicates the solve attempt was unsuccessful.
     - `error`: Detailed error message for debugging.

#### Direct Script Execution

For cases where API use is not feasible, the solver scripts can be run directly in both asynchronous and synchronous modes. This is especially useful for scripts or automation workflows.

1. **Asynchronous Solver**

   The asynchronous solver (`async_solver.py`) is optimal for applications needing high concurrency, as it allows multiple CAPTCHA-solving tasks without blocking other processes.

   **Example Code**:

   ```python
   import asyncio
   from async_solver import AsyncGeetestSolver

   async def solve_captcha():
       # Create an instance of the async solver with debug logging enabled
       solver = AsyncGeetestSolver(debug=True)
       # Attempt to solve the CAPTCHA with the provided sitekey
       result = await solver.solve(sitekey="YOUR_SITEKEY")
       print("Solution:", result.response if result.status == "success" else result.reason)

   asyncio.run(solve_captcha())
   ```

   **Explanation**:

   - `AsyncGeetestSolver(debug=True)`: Initializes the solver with debugging enabled for detailed logs.
   - `await solver.solve(sitekey="YOUR_SITEKEY")`: Runs the CAPTCHA-solving asynchronously, where `sitekey` is the key for the target CAPTCHA.

   **Output**:

   - `result.response`: Contains the solution token if successful.
   - `result.reason`: Provides an error description if solving failed.

2. **Synchronous Solver**

   The synchronous solver (`sync_solver.py`) is suitable for simpler or single-threaded applications where concurrency isn’t essential.

   **Example Code**:

   ```python
   from sync_solver import GeetestSolver

   def solve_captcha():
       # Initialize the synchronous solver with debugging enabled
       solver = GeetestSolver(debug=True)
       # Solve the CAPTCHA using the sitekey
       result = solver.solve(sitekey="YOUR_SITEKEY")
       if result.status == "success":
           print("CAPTCHA Solved:", result.response)
       else:
           print("Failed to solve CAPTCHA:", result.reason)

   solve_captcha()
   ```

   **Explanation**:

   - `GeetestSolver(debug=True)`: Creates a synchronous solver with debug logging enabled.
   - `solver.solve(sitekey="YOUR_SITEKEY")`: Solves the CAPTCHA, returning either a solution token or an error.

   **Output**:

   - `result.response`: Solution token if successful.
   - `result.reason`: Error description if unsuccessful.

#### Understanding Solver Output

Both async and sync solvers return a `GeetestResult` object:

- `response`: The CAPTCHA solution token if solved successfully.
- `elapsed_time_seconds`: Time taken to solve the CAPTCHA.
- `status`: Indicates either `success` or `failure`.
- `reason`: Error message if the solve attempt failed.

#### Enabling Debug Logging

Enable `debug=True` when creating the solver instance to receive detailed logs. Debugging helps track:

- Key steps in the encryption and request process.
- Any failures in CAPTCHA loading, interaction, or validation.
- Response data for troubleshooting.

**Example with Debugging**:

```python
solver = AsyncGeetestSolver(debug=True)
result = await solver.solve(sitekey="YOUR_SITEKEY")
```

#### Troubleshooting Common Issues

- **CAPTCHA Not Solved**: If `status` is `failed`, check `reason` for error details. Common issues include:
  - Network connectivity problems.
  - Invalid or expired `sitekey`.
  - IP bans from excessive requests. Use proxies or adjust the request rate.
- **Timeouts**: If solving takes too long, inspect network settings or retry with different parameters.

---

### ❗ Disclaimers

- Use responsibly; possible risks include API blocking and IP bans.
- This project is for educational and personal use. Star the repository and report issues or request features for future updates.

---

### 📜 ChangeLog

```diff
v0.0.1 ⋮ 11/13/2024
! Initial release

```

---

<p align="center">
  <img src="https://img.shields.io/github/license/sexfrance/Geetest-Solver.svg?style=for-the-badge&labelColor=black&color=f429ff&logo=IOTA"/>
  <img src="https://img.shields.io/github/stars/sexfrance/Geetest-Solver.svg?style=for-the-badge&labelColor=black&color=f429ff&logo=IOTA"/>
  <img src="https://img.shields.io/github/languages/top/sexfrance/Geetest-Solver.svg?style=for-the-badge&labelColor=black&color=f429ff&logo=python"/>
</p>
