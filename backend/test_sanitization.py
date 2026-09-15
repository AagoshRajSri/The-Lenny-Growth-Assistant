from app.agent.sanitize import sanitize_artifact_content

def test_sanitization():
    payload = """<div id="test">Safe text<script>alert('xss')</script><img src="x" onerror="alert(1)" /><a href="javascript:alert(2)">click</a></div>"""
    
    print("Testing HTML sanitization...")
    print(f"RAW PAYLOAD:\n{payload}\n")
    
    sanitized = sanitize_artifact_content(payload, "html")
    print(f"SANITIZED PAYLOAD:\n{sanitized}\n")
    
    assert "<script>" not in sanitized
    assert "onerror" not in sanitized
    assert "javascript:" not in sanitized
    assert "Safe text" in sanitized
    
    print("All assertions passed! Sanitization works securely.")

if __name__ == "__main__":
    test_sanitization()
