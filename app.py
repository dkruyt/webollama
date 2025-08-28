from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
import requests
import json
import os
from dotenv import load_dotenv
import base64
from flask_wtf.csrf import CSRFProtect
import markdown

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
csrf = CSRFProtect(app)

# Ollama API base URL
OLLAMA_API_BASE = os.getenv('OLLAMA_API_BASE', 'http://127.0.0.1:11434')
OLLAMA_API_URL = f"{OLLAMA_API_BASE}/api"

# App configuration
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '127.0.0.1')

@app.route('/')
def index():
    current_version = "Unknown"
    # Get current version from Ollama API
    try:
        response = requests.get(f"{OLLAMA_API_URL}/version")
        if response.status_code == 200:
            version_data = response.json()
            current_version = version_data.get('version', 'Unknown')
    except Exception:
        pass
    return render_template('index.html', version=current_version)

@app.route('/models')
def models():
    try:
        from datetime import datetime
        
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        if response.status_code == 200:
            models_data = response.json()
            models_list = models_data.get('models', [])
            
            # Calculate how long ago each model was modified
            for model in models_list:
                if model.get('modified_at'):
                    try:
                        # Parse ISO 8601 format
                        modified_time = datetime.fromisoformat(model['modified_at'].replace('Z', '+00:00'))
                        now = datetime.now().astimezone()
                        
                        # Calculate time difference in seconds
                        time_diff = (now - modified_time).total_seconds()
                        
                        if time_diff < 60:
                            model['modified_ago'] = f"{int(time_diff)} seconds ago"
                        elif time_diff < 3600:
                            model['modified_ago'] = f"{int(time_diff // 60)} minutes ago"
                        elif time_diff < 86400:
                            model['modified_ago'] = f"{int(time_diff // 3600)} hours ago"
                        elif time_diff < 604800: # 7 days
                            model['modified_ago'] = f"{int(time_diff // 86400)} days ago"
                        elif time_diff < 2592000: # 30 days
                            model['modified_ago'] = f"{int(time_diff // 604800)} weeks ago"
                        else:
                            model['modified_ago'] = f"{int(time_diff // 2592000)} months ago"
                    except Exception:
                        model['modified_ago'] = 'Unknown'
                else:
                    model['modified_ago'] = 'Unknown'
            
            # Get sort params from request
            sort_by = request.args.get('sort', 'name')
            sort_order = request.args.get('order', 'asc')
            
            # Handle sorting
            if sort_by == 'name':
                models_list.sort(key=lambda x: x.get('name', '').lower(), reverse=(sort_order == 'desc'))
            elif sort_by == 'size':
                models_list.sort(key=lambda x: x.get('size', 0), reverse=(sort_order == 'desc'))
            elif sort_by == 'modified':
                models_list.sort(key=lambda x: x.get('modified_at', ''), reverse=(sort_order == 'desc'))
            
            return render_template('models.html', models=models_list, sort_by=sort_by, sort_order=sort_order)
        else:
            flash(f"Error fetching models: {response.status_code}", "danger")
            return render_template('models.html', models=[], sort_by='name', sort_order='asc')
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return render_template('models.html', models=[], sort_by='name', sort_order='asc')

@app.route('/models/<path:model_name>')
def model_detail(model_name):
    try:
        response = requests.post(f"{OLLAMA_API_URL}/show", json={"model": model_name})
        if response.status_code == 200:
            model_info = response.json()
            return render_template('model_detail.html', model=model_info, model_name=model_name)
        else:
            flash(f"Error fetching model details: {response.status_code}", "danger")
            return redirect(url_for('models'))
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return redirect(url_for('models'))

@app.route('/models/delete/<path:model_name>', methods=['POST'])
def delete_model(model_name):
    try:
        response = requests.delete(f"{OLLAMA_API_URL}/delete", json={"model": model_name})
        if response.status_code == 200:
            flash(f"Model {model_name} deleted successfully", "success")
        else:
            flash(f"Error deleting model: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
    return redirect(url_for('models'))

@app.route('/models/update/<path:model_name>')
def update_model(model_name):
    try:
        # Re-pull the model to get the latest version
        response = requests.post(f"{OLLAMA_API_URL}/pull", json={"model": model_name, "stream": False})
        if response.status_code == 200:
            flash(f"Model {model_name} updated successfully", "success")
        else:
            flash(f"Error updating model: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
    return redirect(url_for('models'))

@app.route('/pull', methods=['GET', 'POST'])
def pull_model():
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        try:
            response = requests.post(f"{OLLAMA_API_URL}/pull", json={"model": model_name, "stream": False})
            if response.status_code == 200:
                flash(f"Model {model_name} pulled successfully", "success")
            else:
                flash(f"Error pulling model: {response.status_code}", "danger")
            return redirect(url_for('models'))
        except Exception as e:
            flash(f"Error connecting to Ollama API: {str(e)}", "danger")
            return redirect(url_for('pull_model'))
    return render_template('pull_model.html')

@app.route('/create', methods=['GET'])
def create_model_page():
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        if response.status_code == 200:
            models_data = response.json()
            return render_template('create_model.html', models=models_data.get('models', []))
        else:
            flash(f"Error fetching models: {response.status_code}", "danger")
            return render_template('create_model.html', models=[])
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return render_template('create_model.html', models=[])

@app.route('/create-model', methods=['GET', 'POST'])
def create_model():
    # For GET requests, redirect to the create model page
    if request.method == 'GET':
        return redirect(url_for('create_model_page'))
    
    # Handle POST requests
    # Handle both form data and JSON data
    if request.content_type and 'application/json' in request.content_type:
        # JSON request (from streaming)
        data = request.get_json()
        model_name = data.get('model_name') if data else None
        creation_method = data.get('creation_method') if data else None
        system_prompt = data.get('system_prompt') if data else None
        template = data.get('template') if data else None
        stream = data.get('stream') == 'on' if data else False
        from_model = data.get('from_model') if data else None
        quantize = data.get('quantize') if data else None
    else:
        # Form data request (non-streaming)
        model_name = request.form.get('model_name')
        creation_method = request.form.get('creation_method')
        system_prompt = request.form.get('system_prompt')
        template = request.form.get('template')
        stream = 'stream' in request.form
        from_model = request.form.get('from_model')
        quantize = request.form.get('quantize')
    
    if not model_name:
        flash("Model name is required", "danger")
        return redirect(url_for('create_model_page'))
    
    if not creation_method:
        flash("Creation method is required", "danger")
        return redirect(url_for('create_model_page'))
    
    # Prepare the payload
    payload = {
        "model": model_name,
        "stream": stream
    }
    
    # Add optional parameters if provided
    if system_prompt:
        payload["system"] = system_prompt
    
    if template:
        payload["template"] = template
    
    # Handle creation method
    if creation_method == 'from_model':
        if not from_model:
            flash("Base model is required when creating from an existing model", "danger")
            return redirect(url_for('create_model_page'))
        
        payload["from"] = from_model
        
        # Add quantize if specified
        if quantize:
            payload["quantize"] = quantize
    
    # Handle file-based creation (placeholder for future implementation)
    elif creation_method == 'from_files':
        flash("Creating models from files is not yet implemented in the web interface", "warning")
        return redirect(url_for('create_model_page'))
    
    try:
        if stream:
            return Response(stream_create_model(payload), mimetype='text/event-stream')
        else:
            # Call Ollama API to create the model (non-streaming)
            response = requests.post(f"{OLLAMA_API_URL}/create", json=payload)
            
            if response.status_code == 200:
                flash(f"Model {model_name} created successfully", "success")
            else:
                flash(f"Error creating model: {response.status_code} - {response.text}", "danger")
            
            return redirect(url_for('models'))
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return redirect(url_for('create_model_page'))

def stream_create_model(payload):
    """Stream the model creation process from Ollama API."""
    try:
        # Make streaming request to Ollama API
        response = requests.post(
            f"{OLLAMA_API_URL}/create",
            json=payload,
            stream=True
        )
        
        if response.status_code != 200:
            error_msg = f"Error from Ollama API: {response.status_code}"
            if hasattr(response, 'text'):
                error_msg += f" - {response.text}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            return
        
        for line in response.iter_lines():
            if line:
                try:
                    # Forward the API response directly to the client
                    yield f"data: {line.decode('utf-8')}\n\n"
                except Exception:
                    continue
        
        # Send a final success message
        yield f"data: {json.dumps({'done': True, 'message': 'Model created successfully'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route('/running-models')
def running_models():
    try:
        from datetime import datetime
        
        response = requests.get(f"{OLLAMA_API_URL}/ps")
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('models', [])
            
            # Add expires_in calculation
            for model in models:
                if model.get('expires_at'):
                    # Check if it's the "never expires" sentinel value
                    if model['expires_at'].startswith('0001-01-01'):
                        model['expires_in'] = 'Never'
                    else:
                        # Parse the expiration time
                        try:
                            # Parse ISO 8601 format
                            expiry_time = datetime.fromisoformat(model['expires_at'].replace('Z', '+00:00'))
                            now = datetime.now().astimezone()
                            
                            # Calculate time difference in seconds
                            time_diff = (expiry_time - now).total_seconds()
                            
                            if time_diff <= 0:
                                model['expires_in'] = 'Expired'
                            elif time_diff < 60:
                                model['expires_in'] = f"{int(time_diff)} seconds"
                            elif time_diff < 3600:
                                model['expires_in'] = f"{int(time_diff // 60)} minutes"
                            elif time_diff < 86400:
                                model['expires_in'] = f"{int(time_diff // 3600)} hours"
                            else:
                                model['expires_in'] = f"{int(time_diff // 86400)} days"
                        except Exception:
                            model['expires_in'] = 'Unknown'
                else:
                    model['expires_in'] = 'Never'
            
            return render_template('running_models.html', models=models)
        else:
            flash(f"Error fetching running models: {response.status_code}", "danger")
            return render_template('running_models.html', models=[])
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return render_template('running_models.html', models=[])

@app.route('/models/unload/<path:model_name>', methods=['POST'])
def unload_model(model_name):
    try:
        # Unload model by setting keep_alive to 0
        payload = {
            "model": model_name,
            "prompt": "",
            "keep_alive": "0"
        }
        response = requests.post(f"{OLLAMA_API_URL}/generate", json=payload)

        if response.status_code == 200:
            flash(f"Model {model_name} unloaded successfully", "success")
        else:
            flash(f"Error unloading model: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")

    return redirect(url_for('running_models'))

@app.route('/chat')
def chat():
    # Get available models for the dropdown
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        if response.status_code == 200:
            models_data = response.json()
            return render_template('chat.html', models=models_data.get('models', []))
        else:
            flash(f"Error fetching models: {response.status_code}", "danger")
            return render_template('chat.html', models=[])
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return render_template('chat.html', models=[])

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    model = data.get('model')
    message = data.get('message')
    conversation = data.get('conversation', [])
    stream = data.get('stream', False)
    
    # Format message for Ollama API
    messages = conversation + [{"role": "user", "content": message}]
    
    if stream:
        return stream_chat_response(model, messages)
    
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/chat", 
            json={"model": model, "messages": messages, "stream": False}
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract assistant's message from the response
            assistant_message = result.get('message', {}).get('content', '')
            return jsonify({
                "response": assistant_message,
                "conversation": messages + [{"role": "assistant", "content": assistant_message}]
            })
        else:
            return jsonify({"error": f"Error from Ollama API: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error connecting to Ollama API: {str(e)}"}), 500

def stream_chat_response(model, messages):
    def generate():
        assistant_message = ""
        try:
            # Make streaming request to Ollama API
            response = requests.post(
                f"{OLLAMA_API_URL}/chat",
                json={"model": model, "messages": messages, "stream": True},
                stream=True
            )
            
            if response.status_code != 200:
                error_msg = f"Error from Ollama API: {response.status_code}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                return
                
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'message' in chunk and 'content' in chunk['message']:
                            # Get the content delta
                            content_delta = chunk['message']['content']
                            assistant_message += content_delta
                            yield f"data: {json.dumps({'delta': content_delta, 'content': assistant_message})}\n\n"
                    except json.JSONDecodeError:
                        continue
            
            # Send the final message with the complete conversation
            final_conversation = messages + [{"role": "assistant", "content": assistant_message}]
            yield f"data: {json.dumps({'done': True, 'conversation': final_conversation})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/generate')
def generate():
    # Get available models for the dropdown
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags")
        if response.status_code == 200:
            models_data = response.json()
            return render_template('generate.html', models=models_data.get('models', []))
        else:
            flash(f"Error fetching models: {response.status_code}", "danger")
            return render_template('generate.html', models=[])
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")
        return render_template('generate.html', models=[])

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    model = data.get('model')
    prompt = data.get('prompt')
    system = data.get('system', '')
    options = data.get('options', {})
    
    # Build request payload
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    if system:
        payload["system"] = system
    
    # Convert string values to appropriate types for Ollama API
    if options:
        processed_options = {}
        for key, value in options.items():
            if key in ['num_ctx', 'num_predict', 'num_keep', 'seed', 'top_k']:
                # Convert to integer
                try:
                    processed_options[key] = int(value) if value != '' and value is not None else None
                except (ValueError, TypeError):
                    continue
            elif key in ['temperature', 'top_p', 'repeat_penalty', 'typical_p']:
                # Convert to float
                try:
                    processed_options[key] = float(value) if value != '' and value is not None else None
                except (ValueError, TypeError):
                    continue
            elif key in ['repeat_last_n']:
                # Convert to integer, handle -1 for no limit
                try:
                    processed_options[key] = int(value) if value != '' and value is not None else None
                except (ValueError, TypeError):
                    continue
            elif value != '' and value is not None:  # For other string options
                processed_options[key] = value
        
        # Only add options if we have valid ones
        if processed_options:
            payload["options"] = processed_options
    
    try:
        response = requests.post(f"{OLLAMA_API_URL}/generate", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify(result)
        else:
            return jsonify({"error": f"Error from Ollama API: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error connecting to Ollama API: {str(e)}"}), 500

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/model_help')
def model_help():
    return render_template('model_help.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/version')
def version():
    current_version = "Unknown"
    latest_version = "Unknown"
    update_available = False
    release_date = "Unknown"
    changelog_markdown = None

    # Get current version from Ollama API
    try:
        response = requests.get(f"{OLLAMA_API_URL}/version")
        if response.status_code == 200:
            version_data = response.json()
            current_version = version_data.get('version', 'Unknown')
        else:
            flash(f"Error fetching version: {response.status_code}", "danger")
    except Exception as e:
        flash(f"Error connecting to Ollama API: {str(e)}", "danger")

    # Get latest version from GitHub releases
    try:
        github_response = requests.get("https://api.github.com/repos/ollama/ollama/releases/latest")
        if github_response.status_code == 200:
            github_data = github_response.json()
            latest_version = github_data.get('tag_name', 'Unknown')
            if latest_version.startswith('v'):
                latest_version = latest_version[1:]  # Remove 'v' prefix if present

            # Get release date
            if github_data.get('published_at'):
                from datetime import datetime
                try:
                    published_date = datetime.fromisoformat(github_data['published_at'].replace('Z', '+00:00'))
                    release_date = published_date.strftime('%B %d, %Y')
                except:
                    release_date = "Unknown"

            # Get raw markdown from release body and convert to HTML
            if github_data.get('body'):
                try:
                    # Convert markdown to HTML
                    changelog_markdown = markdown.markdown(github_data['body'], extensions=['extra'])
                except Exception:
                    # If conversion fails, use the raw markdown
                    changelog_markdown = github_data['body']

            # Check if update is available
            if current_version != "Unknown" and latest_version != "Unknown":
                current_parts = current_version.split('.')
                latest_parts = latest_version.split('.')

                # Compare version numbers
                for i in range(max(len(current_parts), len(latest_parts))):
                    current_num = int(current_parts[i]) if i < len(current_parts) else 0
                    latest_num = int(latest_parts[i]) if i < len(latest_parts) else 0

                    if latest_num > current_num:
                        update_available = True
                        break
                    elif current_num > latest_num:
                        break

        else:
            flash(f"Error fetching latest version from GitHub: {github_response.status_code}", "info")
    except Exception as e:
        flash(f"Error connecting to GitHub API: {str(e)}", "info")

    return render_template('version.html',
                          version=current_version,
                          latest_version=latest_version,
                          update_available=update_available,
                          release_date=release_date,
                          changelog_markdown=changelog_markdown)

# The parse_github_release_notes function is no longer used since we're displaying raw markdown

@app.route('/api/check-updates')
def check_updates():
    """API endpoint to check for available updates"""
    try:
        # Get current version
        current_version = "Unknown"
        try:
            response = requests.get(f"{OLLAMA_API_URL}/version")
            if response.status_code == 200:
                version_data = response.json()
                current_version = version_data.get('version', 'Unknown')
        except Exception as e:
            return jsonify({"error": f"Error connecting to Ollama API: {str(e)}"}), 500
        
        # Get latest version from GitHub
        try:
            github_response = requests.get("https://api.github.com/repos/ollama/ollama/releases/latest")
            if github_response.status_code == 200:
                github_data = github_response.json()
                latest_version = github_data.get('tag_name', 'Unknown')
                if latest_version.startswith('v'):
                    latest_version = latest_version[1:]  # Remove 'v' prefix if present
                
                # Check if update is available
                update_available = False
                if current_version != "Unknown" and latest_version != "Unknown":
                    current_parts = current_version.split('.')
                    latest_parts = latest_version.split('.')
                    
                    # Compare version numbers
                    for i in range(max(len(current_parts), len(latest_parts))):
                        current_num = int(current_parts[i]) if i < len(current_parts) else 0
                        latest_num = int(latest_parts[i]) if i < len(latest_parts) else 0
                        
                        if latest_num > current_num:
                            update_available = True
                            break
                        elif current_num > latest_num:
                            break
                
                # Get release date
                release_date = "Unknown"
                if github_data.get('published_at'):
                    from datetime import datetime
                    try:
                        published_date = datetime.fromisoformat(github_data['published_at'].replace('Z', '+00:00'))
                        release_date = published_date.strftime('%B %d, %Y')
                    except:
                        pass
                
                # Get download URLs
                assets = github_data.get('assets', [])
                download_urls = {}
                for asset in assets:
                    name = asset.get('name', '')
                    if name.endswith('.dmg'):
                        download_urls['macos'] = asset.get('browser_download_url')
                    elif name.endswith('.msi'):
                        download_urls['windows'] = asset.get('browser_download_url')
                    elif 'linux' in name.lower() and name.endswith('.tar.gz'):
                        download_urls['linux'] = asset.get('browser_download_url')
                
                return jsonify({
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_available": update_available,
                    "release_date": release_date,
                    "download_urls": download_urls,
                    "release_url": github_data.get('html_url')
                })
            else:
                return jsonify({"error": f"Error fetching GitHub data: {github_response.status_code}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error checking for updates: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
