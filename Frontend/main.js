$(document).ready(function () {

    // Search Bar Functionality
    $('#SearchBar').on('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            $('#SearchBtn').click();
        }
    });

    $('#SearchBtn').click(function() {
        const query = $('#SearchBar').val().trim();
        if (query) {
            console.log('Search query:', query);
            // Add search query to history
            addToHistory(query, 'text');
            // Execute the command
            if (typeof eel !== 'undefined' && typeof eel.allCommands === 'function') {
                eel.allCommands(query);
            }
            // Clear search bar
            $('#SearchBar').val('');
        }
    });

    // Chat History Management
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    
    // Function to add message to history
    function addToHistory(message, type = 'text') {
        const timestamp = new Date().toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        
        const historyItem = {
            message: message,
            type: type, // 'text', 'voice', or 'gemini'
            timestamp: timestamp,
            fullDate: new Date().toISOString()
        };
        
        chatHistory.unshift(historyItem); // Add to beginning
        
        // Keep only last 100 messages
        if (chatHistory.length > 100) {
            chatHistory = chatHistory.slice(0, 100);
        }
        
        // Save to localStorage
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
        
        // Update display if offcanvas is open
        updateChatHistoryDisplay();
    }
    
    // Expose addToHistory to Python
    window.addToChatHistory = addToHistory;
    eel.expose(addToChatHistory, 'addToChatHistory');
    
    // Function to update chat history display
    function updateChatHistoryDisplay() {
        const container = $('#chatHistoryList');
        const emptyMessage = $('#emptyHistoryMessage');
        
        if (chatHistory.length === 0) {
            emptyMessage.show();
            container.empty();
            return;
        }
        
        emptyMessage.hide();
        container.empty();
        
        chatHistory.forEach((item, index) => {
            let typeClass, typeIcon, typeLabel;
            
            if (item.type === 'voice') {
                typeClass = 'voice';
                typeIcon = '<i class="bi bi-mic-fill"></i>';
                typeLabel = 'voice';
            } else if (item.type === 'gemini') {
                typeClass = 'gemini';
                typeIcon = '<i class="bi bi-stars"></i>';
                typeLabel = 'Gemini';
            } else {
                typeClass = 'text';
                typeIcon = '<i class="bi bi-keyboard"></i>';
                typeLabel = 'text';
            }
            
            const historyItem = $(`
                <div class="chat-history-item" data-index="${index}">
                    <div class="chat-time">
                        <i class="bi bi-clock"></i> ${item.timestamp}
                    </div>
                    <div class="chat-message">${item.message}</div>
                    <span class="chat-type ${typeClass}">${typeIcon} ${typeLabel}</span>
                </div>
            `);
            
            // Click to re-run command
            historyItem.click(function() {
                const msg = item.message;
                $('#ChatBox').val(msg);
                ShowHideButton(msg);
                // Close offcanvas
                const offcanvas = bootstrap.Offcanvas.getInstance($('#offcanvasscrolling')[0]);
                if (offcanvas) offcanvas.hide();
            });
            
            container.append(historyItem);
        });
    }
    
    // Clear history button
    $('#clearHistoryBtn').click(function() {
        if (confirm('Are you sure you want to clear all chat history?')) {
            chatHistory = [];
            localStorage.removeItem('chatHistory');
            updateChatHistoryDisplay();
        }
    });
    
    // Update display when offcanvas is shown
    $('#offcanvasscrolling').on('shown.bs.offcanvas', function() {
        updateChatHistoryDisplay();
    });
    
    // Initialize display
    updateChatHistoryDisplay();

    // Simple bounce in and bounce out animation for "Ask me anything" text
    function bounceInText() {
        $(".glowing-text").addClass('bounce-in-effect');
        setTimeout(() => {
            $(".glowing-text").removeClass('bounce-in-effect');
        }, 1000);
    }

    function bounceOutText() {
        $(".glowing-text").addClass('bounce-out-effect');
        setTimeout(() => {
            $(".glowing-text").removeClass('bounce-out-effect');
            // After bounce out, start bounce in again
            setTimeout(bounceInText, 500);
        }, 700);
    }

    // Start the animation cycle
    function startBounceAnimation() {
        bounceInText();
        // After staying visible for 3 seconds, bounce out
        setTimeout(bounceOutText, 3000);
    }

    // Initialize the bounce animation
    startBounceAnimation();

    // Add bounce effect on hover
    $(".glowing-text").hover(
        function () {
            // Mouse enter - quick bounce
            $(this).addClass('quick-bounce');
            setTimeout(() => {
                $(this).removeClass('quick-bounce');
            }, 600);
        }
    );

    // Restart animation cycle on click
    $(".glowing-text").click(function () {
        // Remove any existing animations
        $(this).removeClass('bounce-in-effect bounce-out-effect quick-bounce');
        // Restart the cycle
        setTimeout(startBounceAnimation, 200);
    });

    // SiriWave initialization
    let siriWave = null;
    let isListening = false;

    // Function to show Gemini response on main page
    window.showGeminiResponse = function(text) {
        console.log("Showing Gemini response:", text);
        $('#geminiResponseText').text(text);
        $('#geminiResponse').fadeIn(300);
    };
    
    // Expose function to Python
    eel.expose(showGeminiResponse, 'showGeminiResponse');

    // Function to close Gemini response
    window.closeGeminiResponse = function() {
        console.log("Closing Gemini response");
        $('#geminiResponse').fadeOut(300);
    };
    
    // Close response when clicking outside the content
    $('#geminiResponse').click(function(e) {
        if (e.target.id === 'geminiResponse') {
            closeGeminiResponse();
        }
    });

    // JS function to receive recognition result from Python
    function receiveRecognitionResult(text) {
        console.log("Recognition result from Python:", text);
        if (text && text.trim().length > 0) {
            // Display recognized text in the Siri message area
            $(".siri-message").text(text);
            
            // Add voice commands to history (exclude system messages)
            if (!text.includes("Listening") && 
                !text.includes("Yes,") && 
                !text.includes("How can I help") &&
                !text.includes("Can you repeat") &&
                !text.includes("You typed")) {
                addToHistory(text, 'voice');
            }
        } else {
            $(".siri-message").text("Sorry, I didn't catch that.");
        }
    }

    // JS function to close SiriWave from Python
    function closeSiriWave() {
        console.log("Closing SiriWave from Python command");
        hideSiriWave();
        isListening = false;
        $("#MicBtn").removeClass('active');
    }

    // JS function to activate mic from hotword detection
    function activateMicFromHotword() {
        console.log("🎤 Hotword detected - Activating microphone...");
        
        if (!isListening) {
            // Play assistant sound
            try {
                if (typeof eel !== 'undefined' && typeof eel.playassistantsound === 'function') {
                    eel.playassistantsound();
                }
            } catch (error) {
                console.error("Error playing sound:", error);
            }
            
            // Show SiriWave
            showSiriWave();
            $(".siri-message").text("Listening...");
            
            // Start listening
            try {
                if (typeof eel !== 'undefined' && typeof eel.start_listen === 'function') {
                    eel.start_listen();
                    isListening = true;
                    $("#MicBtn").addClass('active');
                }
            } catch (error) {
                console.error("Error starting recognition:", error);
            }
        }
    }

    // Robustly expose the JS functions so Python can call them
    (function exposeReceiveResult(retries = 10, delay = 300) {
        if (typeof eel !== 'undefined' && typeof eel.expose === 'function') {
            try {
                eel.expose(receiveRecognitionResult, 'receiveRecognitionResult');
                eel.expose(closeSiriWave, 'closeSiriWave');
                eel.expose(activateMicFromHotword, 'activateMicFromHotword');
                console.log('Functions exposed to Python');
                $('#connectionStatus').text('Connected');
            } catch (err) {
                console.warn('Failed to expose functions, retrying...', err);
                if (retries > 0) setTimeout(() => exposeReceiveResult(retries - 1, delay), delay);
                else $('#connectionStatus').text('Connected (partial)');
            }
        } else {
            console.warn('Eel not available yet - retrying expose...');
            if (retries > 0) setTimeout(() => exposeReceiveResult(retries - 1, delay), delay);
            else $('#connectionStatus').text('Disconnected');
        }
    })();

    function initializeSiriWave() {
        console.log("Attempting to initialize SiriWave...");
        
        // If SiriWave already exists, don't create another one
        if (siriWave) {
            console.log("SiriWave already exists, skipping initialization");
            return true;
        }
        
        // Check if SiriWave library is loaded
        if (typeof SiriWave === 'undefined') {
            console.error("SiriWave library not loaded! Check CDN link.");
            return false;
        }

        // Check if container exists
        const container = document.getElementById("siri-container");
        if (!container) {
            console.error("SiriWave container not found!");
            return false;
        }

        // Clear any existing content in the container
        container.innerHTML = '';

        try {
            siriWave = new SiriWave({
                container: container,
                width: 800,
                height: 200,
                style: "ios9",
                amplitude: 1,
                speed: 0.2,
                color: "#0096ff",
                frequency: 6,
                autostart: false  // Don't autostart, we'll start manually
            });
            
            console.log("SiriWave initialized successfully:", siriWave);
            return true;
        } catch (error) {
            console.error("Error initializing SiriWave:", error);
            return false;
        }
    }

    function showSiriWave() {
        console.log("Showing SiriWave...");
        
        // Hide main section and search bar
        $("#oval").hide();
        $("#searchSection").hide();
        
        // Show SiriWave section
        $("#SiriWave").show().removeAttr('hidden');
        
        // Display greeting message
        $(".siri-message").text("Hello, I am your Dude!!");
        console.log("Displaying greeting: Hello, I am your Dude!!");
        
        // Initialize SiriWave only if it doesn't exist
        if (!siriWave) {
            console.log("SiriWave not initialized, initializing now...");
            if (!initializeSiriWave()) {
                console.error("Failed to initialize SiriWave");
                // If initialization fails, go back to main screen
                hideSiriWave();
                return;
            }
        }
        
        // Start the wave animation
        if (siriWave) {
            console.log("Starting SiriWave animation...");
            siriWave.start();
        } else {
            console.error("SiriWave object is null, cannot start animation");
        }
        
        // Change message to "Speak now..." after 2 seconds
        setTimeout(() => {
            $(".siri-message").text("Speak now...");
            console.log("Changed message to: Speak now...");
        }, 2000);
    }

    function hideSiriWave() {
        console.log("Hiding SiriWave...");
        
        // Stop wave animation
        if (siriWave) {
            siriWave.stop();
        }
        
        // Hide SiriWave section
        $("#SiriWave").hide().attr('hidden', true);
        
        // Show main section and search bar
        $("#oval").show();
        $("#searchSection").show();
    }

    function destroySiriWave() {
        console.log("Destroying SiriWave instance...");
        if (siriWave) {
            siriWave.stop();
            // Clear the container
            const container = document.getElementById("siri-container");
            if (container) {
                container.innerHTML = '';
            }
            siriWave = null;
            console.log("SiriWave destroyed");
        }
    }

    // Button click events
    $("#MicBtn").click(function () {
        console.log("=== MIC BUTTON CLICKED ===");
        console.log("Current isListening state:", isListening);
        
        if (!isListening) {
            console.log("🎤 Starting listening mode...");
            
            // Play assistant sound when starting to listen
            console.log("🔊 Playing assistant sound...");
            try {
                if (typeof eel !== 'undefined' && typeof eel.playassistantsound === 'function') {
                    eel.playassistantsound();
                    console.log("✅ Sound function called successfully");
                } else {
                    console.error("❌ Eel or playassistantsound function not available");
                    console.log("Eel object:", typeof eel);
                    console.log("playassistantsound function:", typeof eel?.playassistantsound);
                }
            } catch (error) {
                console.error("❌ Error calling playassistantsound:", error);
            }
            
            // Show SiriWave
            console.log("🌊 Calling showSiriWave...");
            showSiriWave();

            // Show immediate UI feedback that recognition is starting
            $(".siri-message").text("Starting recognition...");

            // Trigger Python speech recognition in background
            try {
                if (typeof eel !== 'undefined' && typeof eel.start_listen === 'function') {
                    eel.start_listen();
                    console.log("✅ Called eel.start_listen() to start recognition");
                } else if (typeof eel !== 'undefined' && eel.start_listen) {
                    // Some eel builds expose functions directly
                    eel.start_listen();
                    console.log("✅ Called eel.start_listen() (fallback)");
                } else {
                    console.warn("start_listen not available on eel yet");
                    $(".siri-message").text("Recognition unavailable (backend not connected)");
                }
            } catch (error) {
                console.error("Error calling eel.start_listen():", error);
                $(".siri-message").text("Error starting recognition");
            }
            
            // Update state
            isListening = true;
            $(this).addClass('active');
            console.log("✅ Mic button state updated - isListening:", isListening);
            
        } else {
            console.log("🛑 Stopping listening mode...");
            hideSiriWave();
            isListening = false;
            $(this).removeClass('active');
        }
        
        console.log("=== MIC BUTTON HANDLER COMPLETE ===");
    });

    // Keyboard shortcut: Windows Key + J to activate voice assistant
    function doc_keyUp(e) {
        // e.metaKey is Cmd on Mac, we need Windows key which is also metaKey on Windows
        // or use Ctrl+Shift+J as alternative
        if ((e.key === "j" || e.key === "J") && (e.metaKey || (e.ctrlKey && e.shiftKey))) {
            console.log("🎹 Keyboard shortcut activated: Win+J or Ctrl+Shift+J");
            
            if (!isListening) {
                // Play assistant sound
                try {
                    if (typeof eel !== 'undefined' && typeof eel.playassistantsound === 'function') {
                        eel.playassistantsound();
                    }
                } catch (error) {
                    console.error("Error playing sound:", error);
                }
                
                // Show SiriWave
                showSiriWave();
                $(".siri-message").text("Starting recognition...");
                
                // Start listening
                try {
                    if (typeof eel !== 'undefined' && typeof eel.start_listen === 'function') {
                        eel.start_listen();
                    }
                } catch (error) {
                    console.error("Error starting recognition:", error);
                }
                
                isListening = true;
                $("#MicBtn").addClass('active');
            }
        }
    }
    document.addEventListener('keyup', doc_keyUp, false);

    // Click anywhere on SiriWave section to close it
    $("#SiriWave").click(function() {
        if (isListening) {
            console.log("SiriWave section clicked, closing...");
            hideSiriWave();
            isListening = false;
            $("#MicBtn").removeClass('active');
        }
    });

    $("#ChatBtn").click(function () {
        console.log("Chat button clicked");
        // Add chat functionality here
    });

    $("#SettingBtn").click(function () {
        console.log("Settings button clicked");
        // Add settings functionality here
    });

    // Note: SiriWave will be initialized only when mic button is clicked
    // This prevents duplicate SiriWave instances

    //siri message animation
    $('.siri-message').textillate({
        loop: true,
        sync: true,
        in: {
            effect: 'fadeInUp',
            delayScale: 1.5,
            delay: 50,
            sync: true,
        },
        out: {
            effect: 'fadeOutDown',
            delayScale: 1.5,
            delay: 50,
            sync: true,
        }
    });     

    // Test SiriWave visibility function
    function testSiriWave() {
        console.log("Testing SiriWave visibility...");
        const container = document.getElementById("siri-container");
        if (container) {
            console.log("SiriWave container found:", container);
            console.log("Container dimensions:", container.offsetWidth, "x", container.offsetHeight);
        } else {
            console.error("SiriWave container not found!");
        }
    }

    // Test mic button functionality
    function testMicButton() {
        console.log("Testing Mic button...");
        const micBtn = document.getElementById("MicBtn");
        if (micBtn) {
            console.log("Mic button found:", micBtn);
            console.log("Mic button has click handler:", micBtn.onclick !== null);
        } else {
            console.error("Mic button not found!");
        }
        
        // Test if SiriWave library is loaded
        console.log("SiriWave library loaded:", typeof SiriWave !== 'undefined');
        
        // Test if eel is available
        console.log("Eel available:", typeof eel !== 'undefined');
    }

    // Call test functions to verify everything is loaded
    setTimeout(testSiriWave, 2000);
    setTimeout(testMicButton, 2500);

    // Hotword detection is now handled by background thread in Python
    // Mic will only activate when "Hey Dude" is detected
    console.log("🎤 Hotword detection active. Say 'Hey Dude' to activate assistant.");




    // Chat feature: Send text commands
    function PlayAssistant(message) {
        if (message && message.trim() !== "") {
            console.log("💬 Sending text command:", message);
            
            // Add to chat history
            addToHistory(message, 'text');
            
            // Don't show SiriWave for text commands - just send directly
            // Clear input and reset buttons
            $("#ChatBox").val("");
            $("#MicBtn").show().removeAttr('hidden');
            $("#SendBtn").hide().attr('hidden', true);
            
            // Send to backend directly
            try {
                eel.allCommands(message);
            } catch (error) {
                console.error("Error sending command:", error);
            }
        }
    }

    // Show/hide Send button based on text input
    function ShowHideButton(message) {
        if (message.length == 0) {
            $("#MicBtn").show().removeAttr('hidden');
            $("#SendBtn").hide().attr('hidden', true);
        } else {
            $("#MicBtn").hide().attr('hidden', true);
            $("#SendBtn").show().removeAttr('hidden');
        }
    }

    // Handle text input changes
    $("#ChatBox").keyup(function(e) {
        let message = $("#ChatBox").val();
        ShowHideButton(message);
        
        // Send on Enter key
        if (e.key === "Enter" || e.keyCode === 13) {
            if (message.trim() !== "") {
                PlayAssistant(message);
            }
        }
    });
    
    // Send button click handler
    $("#SendBtn").click(function() {
        let message = $("#ChatBox").val();
        PlayAssistant(message);
    });
    
    // Initially hide Send button
    $("#SendBtn").hide().attr('hidden', true);



});