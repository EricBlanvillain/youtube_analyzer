#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the indentation in the problem area
fixed_lines = []
for i, line in enumerate(lines):
    if i+1 == 1292:  # The "with st.expander" line
        fixed_lines.append('            with st.expander("Advanced Options"):\n')
    elif i+1 == 1293:  # The first checkbox line
        fixed_lines.append('                use_ssl_workaround = st.checkbox("Enable SSL/TLS workaround", value=True,\n')
    elif i+1 == 1294:  # The help text for checkbox
        fixed_lines.append('                                         help="Use this if you\'re experiencing SSL connection issues")\n')
    elif i+1 == 1295:  # The slider line
        fixed_lines.append('                retry_count = st.slider("Maximum retries:", 1, 5, 3,\n')
    elif i+1 == 1296:  # The help text for slider
        fixed_lines.append('                                    help="Number of times to retry API calls if they fail")\n')
    else:
        fixed_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(fixed_lines)

print("Indentation fixed in app.py")
