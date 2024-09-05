document.addEventListener('DOMContentLoaded', function () {
    const queryInput = document.getElementById('queryInput');
    const submitButton = document.getElementById('submitButton');
    const selectTagButton = document.getElementById('selectTagButton');
    const resultDiv = document.getElementById('result');
    const serverCheckButton = document.getElementById('serverCheck');
    const creatorButton = document.getElementById('creatorButton');
    const creatorWindow = document.getElementById('creator-wrapper');
    const creatorClose = document.getElementById('creatorClose');
    const helpWrapper = document.getElementById('help-wrapper');
    const helpButton = document.getElementById('helpButton');
    const helpClose = document.getElementById('helpClose');
    const clearConvo = document.getElementById('ClearConvo');
    const settingsButton = document.getElementById('settingMenuBtn');
    const settingsWindow = document.getElementById('settings-wrapper');
    const settingsClose = document.getElementById('settingsClose');
    const modelSelect = document.getElementById('modelSelect');
    const changeModelButton = document.getElementById('changeModel');
    const serverIP = document.getElementById('serverIP');
    const serverPort = document.getElementById('serverPort');
    //   const serverStart = document.getElementById('serverStart');

    var creatorContentOpen = false;
    var helpContentOpen = false;
    var code_response = null;

    var ip = '127.0.0.1';
    var port = '8080';
    var url = 'http://' + ip + ':' + port + '/';

    function set_value_of_ip_and_port() {
        serverIP.value = ip;
        serverPort.value = port;
    }
    // get the current ip and port from the settings
    serverIP.addEventListener('change', function () {
        ip = serverIP.value;
        url = 'http://' + ip + ':' + port + '/';
        console.log(url)
    });

    serverPort.addEventListener('change', function () {
        port = serverPort.value;
        url = 'http://' + ip + ':' + port + '/';
        console.log(url)
    });


    // if the settings are open get the current model selected in modelSelect and send it to the server to be loaded
    changeModelButton.addEventListener('click', function () {
        var model = modelSelect.options[modelSelect.selectedIndex].value;
        console.log(model);
        //load the model url
        var req_url = 'http://' + ip + ':' + port + '/load_model';
        fetch(req_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',

            },
            mode: 'cors',
            body: JSON.stringify({ model: model }),
        })
            .then(response => response.json())
            .then(data => {
                console.log("Received data:", data);

                // Check if data.current_model is defined
                if (data.current_model) {
                    // change the current model
                    document.getElementById('modelLoaded').innerText = data.current_model;
                } else {
                    console.log("No current_model data found.");
                }
            })
            .catch(error => {
                console.error("Error:", error);
            });
    });

    function saveQuestionAndResponse(question, response) {
        const savedData = JSON.parse(localStorage.getItem('savedCoversation')) || [];
        savedData.push({ question, response });
        localStorage.setItem('savedCoversation', JSON.stringify(savedData));
    }

    // Function to recover and display saved questions and responses
    function displaySavedData() {
        const savedData = JSON.parse(localStorage.getItem('savedCoversation')) || [];
        for (const entry of savedData) {
            resultDiv.innerHTML += `<div class="user">You said: ${entry.question}</div>`;
            resultDiv.innerHTML += `<div class="bot">Response: ${entry.response}</div>`;
        }
    }

    function clearSavedData() {
        localStorage.removeItem('savedCoversation');
        resultDiv.innerHTML = '';
    }

    // Call this function to display saved data when the window is opened
    displaySavedData();

    resultDiv.addEventListener('click', function (event) {
        if (event.target.id === 'copyCode') {
            console.log('copying code');
            // Code to copy the text when the copy button is clicked
            var div = event.target.parentNode;
            console.log(div);
            var code = div.innerText;
            // replace the last word copy with nothing
            code = code.slice(0, -4);
            console.log(code);
            navigator.clipboard.writeText(code);
        }
    });

    queryInput.addEventListener('keyup', function (event) {
        if (event.key === 'Enter') {
            if (queryInput.value === '') {
                return;
            } else {
                submitButton.click();
                queryInput.value = '';
            }
        }
    });

    clearConvo.addEventListener('click', function () {
        clearSavedData();
        resultDiv.innerHTML = '';
    });

    creatorButton.addEventListener('click', function () {
        if (creatorContentOpen) {
            creatorContentOpen = false;
            creatorWindow.style.display = 'none';
        } else {
            creatorContentOpen = true;
            creatorWindow.style.display = 'block';
        }
    });

    creatorClose.addEventListener('click', function () {
        creatorContentOpen = false;
        creatorWindow.style.display = 'none';
    });

    helpButton.addEventListener('click', function () {
        if (helpContentOpen) {
            helpContentOpen = false;
            helpWrapper.style.display = 'none';
        } else {
            helpContentOpen = true;
            helpWrapper.style.display = 'block';
        }
    });

    helpClose.addEventListener('click', function () {
        helpContentOpen = false;
        helpWrapper.style.display = 'none';
    });

    settingsButton.addEventListener('click', function () {
        if (settingsWindow.style.display === 'block') {
            settingsWindow.style.display = 'none';
        } else {
            settingsWindow.style.display = 'block';
            set_value_of_ip_and_port();
            get_current_model();

            get_ggufs();
        }
    });

    function get_current_model() {
        // get the current model from the server
        var req_url = 'http://' + ip + ':' + port + '/get_current_model';
        fetch(req_url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            mode: 'cors',
        })
            .then(response => response.json())
            .then(data => {
                console.log("Received data:", data);

                // Check if data.current_model is defined
                if (data.current_model) {
                    // set the current model
                    document.getElementById('modelLoaded').innerText = data.current_model;
                } else {
                    console.log("No current_model data found.");
                }
            })
            .catch(error => {
                console.error("Error:", error);
            });
    }

    function get_ggufs() {
        // get models from the server
        var req_url = 'http://' + ip + ':' + port + '/get_gguf_files';
        fetch(req_url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            mode: 'cors',
        })
            .then(response => response.json())
            .then(data => {
                console.log("Received data:", data);

                // Check if data.gguf_files is defined
                if (data.gguf_files && data.gguf_files.length) {
                    // remove the current options
                    var select = document.getElementById('modelSelect');
                    var length = select.options.length;
                    for (i = length - 1; i >= 0; i--) {
                        select.options[i] = null;
                    }

                    // add the new options
                    for (var i = 0; i < data.gguf_files.length; i++) {
                        var opt = document.createElement('option');
                        opt.value = data.gguf_files[i];
                        opt.innerHTML = data.gguf_files[i];
                        select.appendChild(opt);
                    }
                } else {
                    console.log("No gguf_files data found.");
                }
            })
            .catch(error => {
                console.error("Error:", error);
            });
    }

    settingsClose.addEventListener('click', function () {
        settingsWindow.style.display = 'none';
    });


    serverCheckButton.addEventListener('click', function () {
        // guery the server to check if it is running
        // if you get a response then turn the button green
        // if you don't get a response then turn the button red
        var req_url = 'http://' + ip + ':' + port + '/health';
        fetch(req_url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            mode: 'cors',
        })
            .then(response => response.json())
            .then(data => {
                serverCheckButton.style.backgroundColor = 'green';
            })
            .catch(error => {
                serverCheckButton.style.backgroundColor = 'red';
            });
    })

    function getPageContent(callback) {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (chrome.runtime.lastError) {
                console.error("Error querying tabs:", chrome.runtime.lastError);
                callback({ url: "", content: "" });
                return;
            }

            const tabId = tabs[0].id;
            const tabUrl = tabs[0].url;


            chrome.tabs.sendMessage(tabId, { action: "getPageContent" }, function (response) {
                if (chrome.runtime.lastError) {
                    console.error("Error sending message:", chrome.runtime.lastError);
                    callback({ url: tabUrl, content: "" });
                    return;
                }
                callback({ url: tabUrl, content: response ? response.content : "" });
            });
        });
    }
    // Function to update the button appearance based on inspector status
    function updateButtonState(isActive) {
        if (isActive) {
            selectTagButton.classList.add('active');
        } else {
            selectTagButton.classList.remove('active');
        }
    }

    // Function to toggle the inspector
    function toggleInspector() {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            const action = "inspectorTrigger";
            chrome.tabs.sendMessage(tabs[0].id, { action }, function (response) {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError.message);
                    return;
                }
                console.log("Inspector status:", response.status);
                updateButtonState(response.status);
            });
        });
    }

    // Event listener for the button click
    selectTagButton.addEventListener('click', function () {
        toggleInspector();
    });

    function checkInspectorStatus() {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            const action = "isInspectorActive";
            chrome.tabs.sendMessage(tabs[0].id, { action }, function (response) {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError.message);
                    updateButtonState(false); // Assume inactive if there's an error
                    return;
                }
                updateButtonState(response.status);
            });
        });
    }

    chrome.tabs.onActivated.addListener(function (activeInfo) {
        chrome.tabs.get(activeInfo.tabId, function (tab) {
            checkInspectorStatus();
        });
    });

    chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
        if (changeInfo.status === 'complete') {
            checkInspectorStatus();
        }
    });

    checkInspectorStatus();

    //submitButton.addEventListener('click', function () {
    //    const query = queryInput.value;
    //    
    //    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    //        chrome.tabs.sendMessage(tabs[0].id, { action: "getSelectedHMTL" }, function (response) {
    //            console.log(response.selected);
    //            if (response.selected) {
    //                // Если selectedHTML выбран, отправляем его
    //                console.log('Sending selected HTML instead of page content');
    //                sendRequest(query, "", response.selected);
    //            } else {
    //                // Если selectedHTML не выбран, получаем содержимое страницы и отправляем его
    //                console.log('Sending full page content');
    //                getPageContent((pageData) => {
    //                    sendRequest(query, pageData.url, pageData.content);
    //                });
    //            }
    //    
    //            // Отображаем запрос и сообщение "Llama is thinking..."
    //            resultDiv.innerHTML += `<div class="user">You: ${query}</div>`;
    //            resultDiv.innerHTML += `<div class="loading">"Llama is thinking..."</div>`;
    //            resultDiv.scrollTop = resultDiv.scrollHeight;
    //        });
    //    });
    //});

    submitButton.addEventListener('click', function () {
        const query = queryInput.value;

        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            chrome.tabs.sendMessage(tabs[0].id, { action: "getSelectedHMTL" }, function (response) {
                if (response.selected !== "") {
                    console.log('Sending selected HTML instead of page content');
                    //toggleInspector();
                    checkInspectorStatus()
                    sendRequest(query, tabs[0].url, response.selected);
                } else {
                    console.log('Sending full page content');
                    getPageContent((pageData) => {
                        sendRequest(query, pageData.url, pageData.content);
                    });
                }

                // Отображаем запрос и сообщение "Llama is thinking..."
                resultDiv.innerHTML += `<div class="user">You: ${query}</div>`;
                resultDiv.innerHTML += `<div class="loading">"Llama is thinking..."</div>`;
                resultDiv.scrollTop = resultDiv.scrollHeight;
            });
        });
    });


    function sendRequest(query, pageUrl, pageContent) {
        const req_url = 'http://' + ip + ':' + port + '/query';
        let accumulatedResponse = ''; // Declare accumulatedResponse in the outer scope
        let isStreamEnded = false; // Flag to track if the stream has ended

        fetch(req_url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, page_url: pageUrl, page_content: pageContent }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                return new ReadableStream({
                    start(controller) {
                        function push() {
                            reader.read().then(({ done, value }) => {
                                if (done) {
                                    controller.close();
                                    isStreamEnded = true; // Set the flag when the stream ends
                                    return;
                                }
                                const chunk = decoder.decode(value, { stream: true });
                                accumulatedResponse += chunk; // Append to the outer variable
                                updateUI(accumulatedResponse, !isStreamEnded); // Pass the streaming state
                                push();
                            });
                        }
                        push();
                    }
                });
            })
            .then(stream => stream.pipeThrough(new TextDecoderStream())) // Decode the stream
            .then(decoderStream => {
                const reader = decoderStream.getReader();
                return new Promise((resolve, reject) => {
                    function read() {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                const loading = document.querySelector('.loading');
                                if (loading) {
                                    loading.parentNode.removeChild(loading);
                                }
                                resolve();
                                return;
                            }
                            accumulatedResponse += value; // Append to the outer variable
                            updateUI(accumulatedResponse, !isStreamEnded); // Pass the streaming state
                            read();
                        });
                    }
                    read();
                });
            })
            .then(() => {
                // The stream has ended, update the UI with the complete response and finalize
                if (isStreamEnded) {
                    const finalResponse = resultDiv.querySelector('.bot-stream');
                    if (finalResponse) {
                        finalResponse.classList.remove('bot-stream');
                        finalResponse.classList.add('bot');
                        // Optionally, you can also update the text here if needed
                        // finalResponse.innerHTML = `Response: ${accumulatedResponse}`;
                    }
                    saveQuestionAndResponse(query, accumulatedResponse);
                    queryInput.value = '';
                }
            })
            .catch(error => {
                resultDiv.innerHTML += `<div class="error">${error}, is the server up?</div>`;
            });
    }

    function updateUI(text, incompleted) {
        // Remove any existing bot response
        if (incompleted) {
            const existingBotResponse = resultDiv.querySelector('.bot-stream');
            if (existingBotResponse) {
                existingBotResponse.parentNode.removeChild(existingBotResponse);
            }
        }

        // Process the text (similar to what you did in the original code)
        text = text.replace(/(?:\r\n|\r|\n)/g, '<br>');
        text = text.replace(/\. \*/g, '\n');
        text = text.replace(/\. \d/g, '\n');

        const codeResponse = text.match(/```(.*?)```/g);
        if (codeResponse) {
            text = text.replace(/```<br>/g, '```');
            text = text.replace(/```python/g, '```');
            text = text.replace(/```javascript/g, '```');
            text = text.replace(/```(.*?)```/g, '<div class="code"><pre>$1</pre><div id="copyCode">copy</div></div>');
        }
        if (incompleted) {
            resultDiv.innerHTML += `<div class="bot-stream">Response: ${text}</div>`;
        }
        else {
            resultDiv.innerHTML += `<div class="bot">Response: ${text}</div>`;
        }

        resultDiv.scrollTop = resultDiv.scrollHeight;
    }
});
