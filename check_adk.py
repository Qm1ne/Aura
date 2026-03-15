import google.adk.sessions as sessions
import inspect

print("Checking VertexAiSessionService...")
if hasattr(sessions, "VertexAiSessionService"):
    cls = sessions.VertexAiSessionService
    print(f"Found: {cls}")
    print(f"Init: {inspect.signature(cls.__init__)}")
else:
    print("Not found in google.adk.sessions. Checking for alternate names...")
    for name in dir(sessions):
        if "SessionService" in name:
            print(f"- {name}")
