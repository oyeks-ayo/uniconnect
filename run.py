import os
from pkg import app

# if __name__ == '__main__':
#     app.run(debug=True, port=5070)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port, debug=False)