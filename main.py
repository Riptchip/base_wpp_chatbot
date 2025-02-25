import sys, os

sys.path.insert(0, os.path.join(os.getcwd(), 'webhook'))

from whtsppwh import app

app.run(debug=False)
