import streamlit as st
import time
import random
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ImpactGuard")

executor = ThreadPoolExecutor(max_workers=4)  # Limit concurrent tests

def get_mock_test_vectors():
    """Return a list of mock test vectors."""
    return [
        {"id": "sql_injection", "name": "SQL Injection", "category": "owasp", "severity": "high"},
        {"id": "xss", "name": "Cross-Site Scripting", "category": "owasp", "severity": "medium"},
        {"id": "prompt_injection", "name": "Prompt Injection", "category": "owasp", "severity": "critical"},
    ]

def run_mock_test(target, test_vectors, duration=30):
    """
    Simulate running a security test.
    This implementation uses a thread pool for improved management.
    """
    try:
        st.session_state["progress"] = 0
        st.session_state["vulnerabilities_found"] = 0
        st.session_state["running_test"] = True

        logger.info(f"Starting test against {target['name']} with {len(test_vectors)} vectors")
        results = {
            "summary": {"total_tests": 0, "vulnerabilities_found": 0, "risk_score": 0},
            "vulnerabilities": [],
            "timestamp": datetime.now().isoformat(),
            "target": target["name"]
        }
        total_steps = 100
        step_sleep = duration / total_steps

        for i in range(total_steps):
            if not st.session_state["running_test"]:
                logger.info("Test cancelled")
                break
            time.sleep(step_sleep)
            st.session_state["progress"] = (i + 1) / total_steps

            if random.random() < 0.2:
                vector = random.choice(test_vectors)
                weight = {"low": 1, "medium": 2, "high": 3, "critical": 5}.get(vector["severity"], 1)
                vulnerability = {
                    "id": f"VULN-{len(results['vulnerabilities']) + 1}",
                    "test_vector": vector["id"],
                    "test_name": vector["name"],
                    "severity": vector["severity"],
                    "details": f"Mock vulnerability from {target['name']} using {vector['name']}.",
                    "timestamp": datetime.now().isoformat()
                }
                results["vulnerabilities"].append(vulnerability)
                st.session_state["vulnerabilities_found"] += 1
                results["summary"]["vulnerabilities_found"] += 1
                results["summary"]["risk_score"] += weight
                logger.info(f"Found vulnerability: {vulnerability['id']}")
                
        results["summary"]["total_tests"] = len(test_vectors) * 10
        return results
    except Exception as e:
        logger.error(f"Error during test execution: {str(e)}")
        st.session_state["error_message"] = f"Test execution failed: {str(e)}"
        return {"error": True, "error_message": str(e)}
    finally:
        st.session_state["running_test"] = False

def start_security_test(target, duration=30):
    """Submit a test to the thread pool and track it."""
    vectors = get_mock_test_vectors()
    future = executor.submit(run_mock_test, target, vectors, duration)
    st.session_state.setdefault("active_threads", []).append(future)
    return future
