"""Python Bridge for Production Automation - Universal Remote API
A FastAPI server that executes Selenium commands atomically.
Author: QA Automation Engineer
Date: January 14, 2026
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from seleniumbase import Driver
from selenium import webdriver  # For LambdaTest RemoteWebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import uuid
import requests
from datetime import datetime
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Python Bridge API",
    description="Production-ready Selenium automation bridge for n8n",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for JSON Schema
class TestStep(BaseModel):
    action: str = Field(..., description="Action to perform: open_url, click, type_text, verify, wait, screenshot")
    selector: Optional[str] = Field(None, description="CSS selector for the element")
    value: Optional[str] = Field(None, description="Value for type or verify actions")
    timeout: Optional[int] = Field(10, description="Timeout in seconds")
    description: Optional[str] = Field(None, description="Human-readable description of the step")

class TestRequest(BaseModel):
    test_id: str = Field(..., description="Unique test identifier")
    url: str = Field(..., description="Starting URL for the test")
    steps: List[TestStep] = Field(..., description="List of test steps to execute")
    browser: Optional[str] = Field("chrome", description="Browser to use (chrome, firefox, edge)")
    headless: Optional[bool] = Field(True, description="Run browser in headless mode")
    webhook_url: Optional[str] = Field(None, description="n8n webhook URL to send results")

class TestResult(BaseModel):
    test_id: str
    status: str  # PASS, FAIL, ERROR
    duration: float
    steps_executed: int
    steps_passed: int
    steps_failed: int
    error_message: Optional[str] = None
    screenshot_url: Optional[str] = None
    timestamp: str
    detailed_results: List[Dict[str, Any]]

# Global driver management (session-based)
active_drivers: Dict[str, Driver] = {}

# Create screenshots directory
SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ============= CORE EXECUTION ENGINE =============

class SeleniumExecutor:
    """Atomic executor for Selenium commands with built-in retry and error handling."""
    
    def __init__(self, driver: Driver, test_id: str):
        self.driver = driver
        self.test_id = test_id
        self.step_results = []
        
    def execute_step(self, step: TestStep, step_number: int) -> Dict[str, Any]:
        """Execute a single atomic step with retry logic."""
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                result = self._execute_action(step, step_number)
                result['attempt'] = attempt + 1
                result['status'] = 'passed'
                logger.info(f"Step {step_number} passed: {step.action}")
                return result
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Step {step_number} failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying...")
                    time.sleep(retry_delay)
                else:
                    # Final attempt failed - take screenshot
                    screenshot_path = self._capture_failure_screenshot(step_number)
                    result = {
                        'step_number': step_number,
                        'action': step.action,
                        'status': 'failed',
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'screenshot': screenshot_path,
                        'attempt': attempt + 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.error(f"Step {step_number} failed after {max_retries + 1} attempts: {str(e)}")
                    return result
        
    def _execute_action(self, step: TestStep, step_number: int) -> Dict[str, Any]:
        """Execute the actual Selenium action."""
        start_time = time.time()
        
        if step.action == "open_url":
            url = step.value or step.selector
            self.driver.get(url)
            # Wait for page to load completely
            time.sleep(1)  # Simple wait for page load            
        elif step.action == "click":
            if not step.selector:
                raise ValueError("Selector is required for click action")
            WebDriverWait(self.driver, step.timeout or 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))
            self.driver.click(step.selector)
            
        elif step.action == "type_text":
            if not step.selector or not step.value:
                raise ValueError("Selector and value are required for type_text action")
            WebDriverWait(self.driver, step.timeout or 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))
            self.driver.type(step.selector, step.value)
            
        elif step.action == "verify":
            if not step.selector:
                raise ValueError("Selector is required for verify action")
            element = WebDriverWait(self.driver, step.timeout or 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))
            if step.value:
                element_text = element.text
                if step.value not in element_text:
                    raise AssertionError(f"Expected '{step.value}' not found in element text: '{element_text}'")
                    
        elif step.action == "wait":
            wait_time = int(step.value) if step.value else step.timeout
            time.sleep(wait_time)
            
        elif step.action == "screenshot":
            screenshot_path = f"{SCREENSHOTS_DIR}/{self.test_id}_step_{step_number}.png"
            self.driver.save_screenshot(screenshot_path)
            return {
                'step_number': step_number,
                'action': step.action,
                'screenshot': screenshot_path,
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
        else:
            raise ValueError(f"Unknown action: {step.action}")
        
        duration = time.time() - start_time
        return {
            'step_number': step_number,
            'action': step.action,
            'selector': step.selector,
            'value': step.value,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
    
    def _capture_failure_screenshot(self, step_number: int) -> str:
        """Capture screenshot when a step fails."""
        try:
            screenshot_path = f"{SCREENSHOTS_DIR}/{self.test_id}_step_{step_number}_FAILED.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Failure screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            return None

# ============= API ENDPOINTS =============

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "service": "Python Bridge API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_drivers)
    }

@app.post("/execute-test", response_model=TestResult)
async def execute_test(request: TestRequest, background_tasks: BackgroundTasks):
    """
    Execute a test with atomic step execution.
    Each step is retried automatically on failure.
    Results are sent back to n8n webhook if provided.
    """
    start_time = time.time()
    driver = None
    
    try:
        logger.info(f"Starting test execution: {request.test_id}")
        
        # Initialize SeleniumBase driver
        driver = Driver(
            browser=request.browser,
            headless=request.headless,
            uc=True,  # Use undetected-chromedriver
            page_load_strategy="normal"
        )
        
        # Store driver for potential reuse
        session_id = str(uuid.uuid4())
        active_drivers[session_id] = driver
        
        # Create executor
        executor = SeleniumExecutor(driver, request.test_id)
        
        # Open initial URL
        logger.info(f"Opening URL: {request.url}")
        driver.get(request.url)
#         driver.wait_for_ready_state_complete()
        
        # Execute all steps
        detailed_results = []
        steps_passed = 0
        steps_failed = 0
        
        for idx, step in enumerate(request.steps, 1):
            logger.info(f"Executing step {idx}/{len(request.steps)}: {step.action}")
            step_result = executor.execute_step(step, idx)
            detailed_results.append(step_result)
            
            if step_result['status'] == 'passed':
                steps_passed += 1
            else:
                steps_failed += 1
                # Optionally stop on first failure for critical paths
                # break
        
        # Determine overall test status
        duration = time.time() - start_time
        overall_status = "PASS" if steps_failed == 0 else "FAIL"
        
        result = TestResult(
            test_id=request.test_id,
            status=overall_status,
            duration=round(duration, 2),
            steps_executed=len(request.steps),
            steps_passed=steps_passed,
            steps_failed=steps_failed,
            timestamp=datetime.now().isoformat(),
            detailed_results=detailed_results
        )
        
        # Send webhook callback to n8n if provided
        if request.webhook_url:
            background_tasks.add_task(send_webhook, request.webhook_url, result.dict())
        
        logger.info(f"Test completed: {request.test_id} - Status: {overall_status}")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Test execution failed: {error_msg}")
        logger.error(traceback.format_exc())
        
        # Capture error screenshot
        screenshot_path = None
        if driver:
            try:
                screenshot_path = f"{SCREENSHOTS_DIR}/{request.test_id}_ERROR.png"
                driver.save_screenshot(screenshot_path)
            except:
                pass
        
        result = TestResult(
            test_id=request.test_id,
            status="ERROR",
            duration=round(duration, 2),
            steps_executed=0,
            steps_passed=0,
            steps_failed=0,
            error_message=error_msg,
            screenshot_url=screenshot_path,
            timestamp=datetime.now().isoformat(),
            detailed_results=[]
        )
        
        if request.webhook_url:
            background_tasks.add_task(send_webhook, request.webhook_url, result.dict())
        
        return result
        
    finally:
        # Cleanup driver
        if driver:
            try:
                driver.quit()
                # Remove from active sessions
                for sid, d in list(active_drivers.items()):
                    if d == driver:
                        del active_drivers[sid]
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")

def send_webhook(webhook_url: str, data: Dict):
    """Send test results to n8n webhook."""
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {str(e)}")

# ============= MAIN =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
