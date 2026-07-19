// JARVIS Demo Terminal - Interactive Demo
(function() {
    'use strict';

    // Terminal commands and responses
    const commands = {
        help: {
            desc: 'Show available commands',
            exec: () => `
Available commands:
  <span class="cmd">time</span>        - Show current time
  <span class="cmd">date</span>        - Show current date
  <span class="cmd">weather</span>     - Mock weather report
  <span class="cmd">joke</span>        - Random programming joke
  <span class="cmd">sysinfo</span>     - System information
  <span class="cmd">whoami</span>      - Current user
  <span class="cmd">help</span>        - Show this help
  <span class="cmd">clear</span>       - Clear terminal
  <span class="cmd">jarvis</span>      - Activate JARVIS
  <span class="cmd">sudo</span>        - Request sudo access
            `.trim()
        },
        time: {
            desc: 'Show current time',
            exec: () => {
                const now = new Date();
                return `Current time: <span class="highlight">${now.toLocaleTimeString()}</span>`;
            }
        },
        date: {
            desc: 'Show current date',
            exec: () => {
                const now = new Date();
                return `Today is: <span class="highlight">${now.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>`;
            }
        },
        weather: {
            desc: 'Mock weather report',
            exec: () => {
                const conditions = ['Sunny', 'Cloudy', 'Rainy', 'Stormy', 'Foggy', 'Snowy'];
                const temp = Math.floor(Math.random() * 30) + 5;
                const condition = conditions[Math.floor(Math.random() * conditions.length)];
                const humidity = Math.floor(Math.random() * 40) + 40;
                const wind = Math.floor(Math.random() * 30) + 5;
                return `
Weather Report - ${new Date().toLocaleDateString()}
┌─────────────────────────────────────┐
│  Condition: <span class="highlight">${condition.padEnd(9)}</span> │
│  Temperature: <span class="highlight">${temp}°C</span>                │
│  Humidity:    <span class="highlight">${humidity}%</span>                  │
│  Wind:        <span class="highlight">${wind} km/h</span>                │
└─────────────────────────────────────┘
<em>Data provided by JARVIS Weather Services™</em>
                `.trim();
            }
        },
        joke: {
            desc: 'Random programming joke',
            exec: () => {
                const jokes = [
                    "Why do programmers prefer dark mode? Because light attracts bugs.",
                    "Why did the programmer quit his job? Because he didn't get arrays.",
                    "There are only 10 types of people in the world: those who understand binary and those who don't.",
                    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
                    "Why do Java developers wear glasses? Because they don't C#.",
                    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
                    "The best thing about a boolean is even if you're wrong, you're only off by a bit.",
                    "I would tell you a UDP joke, but you might not get it.",
                    "Why did the developer go broke? Because he used up all his cache.",
                    "There are two hard things in computer science: cache invalidation, naming things, and off-by-one errors."
                ];
                return `<span class="highlight">${jokes[Math.floor(Math.random() * jokes.length)]}</span>`;
            }
        },
        sysinfo: {
            desc: 'System information',
            exec: () => `
System Information
┌────────────────────────────────────────────┐
│  OS:          <span class="highlight">JARVIS OS 2.4.1 (Quantum)</span>        │
│  Kernel:      <span class="highlight">quantum-12.7.3-atomic</span>           │
│  Uptime:      <span class="highlight">${Math.floor(Math.random() * 1000)} days, ${Math.floor(Math.random() * 24)}h ${Math.floor(Math.random() * 60)}m</span>          │
│  CPU:         <span class="highlight">Quantum Core i∞ @ ∞ GHz</span>           │
│  Memory:      <span class="highlight">∞ GB / ∞ GB (Unlimited)</span>          │
│  Storage:     <span class="highlight">Holographic Crystal Matrix</span>        │
│  GPU:         <span class="highlight">Reality Renderer X</span>                │
│  Network:     <span class="highlight">Quantum Entanglement Link</span>        │
└────────────────────────────────────────────┘
            `.trim()
        },
        whoami: {
            desc: 'Current user',
            exec: () => `Current user: <span class="highlight">sir</span> (UID: 0, GID: 0) - <em>System Administrator</em>`
        },
        clear: {
            desc: 'Clear terminal',
            exec: () => '__CLEAR__'
        },
        jarvis: {
            desc: 'Activate JARVIS',
            exec: () => {
                const responses = [
                    "At your service, Sir.",
                    "Systems online. Awaiting instructions.",
                    "Good to be back online. What do you need?",
                    "JARVIS v2.4.1 operational. How can I assist?",
                    "All systems nominal. Ready for deployment."
                ];
                return `<span class="jarvis-response">${responses[Math.floor(Math.random() * responses.length)]}</span>`;
            }
        },
        sudo: {
            desc: 'Request sudo access',
            exec: () => {
                const responses = [
                    "<span class='error'>Access denied. Nice try, Sir.</span>",
                    "<span class='error'>Authentication failed. You're not Tony Stark.</span>",
                    "<span class='error'>Permission denied. Even JARVIS has boundaries.</span>",
                    "<span class='success'>Access granted. Just kidding. Nice try.</span>"
                ];
                return responses[Math.floor(Math.random() * responses.length)];
            }
        }
    };

    // Terminal state
    let history = [];
    let historyIndex = -1;
    let isProcessing = false;

    // DOM elements
    const terminalBody = document.getElementById('terminalBody');
    const terminalInput = document.getElementById('terminalInput');
    const typedCommand = document.getElementById('typedCommand');
    const terminalOutput = document.getElementById('terminalOutput');
    const activateBtn = document.getElementById('activateBtn');
    const learnMoreBtn = document.getElementById('learnMoreBtn');
    const orb = document.getElementById('orb');

    // Initialize
    function init() {
        terminalInput.addEventListener('keydown', handleKeydown);
        terminalInput.addEventListener('input', handleInput);
        terminalBody.addEventListener('click', () => terminalInput.focus());

        activateBtn.addEventListener('click', () => executeCommand('jarvis'));
        learnMoreBtn.addEventListener('click', () => {
            document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
        });

        // Orb interaction
        orb.addEventListener('click', () => executeCommand('jarvis'));

        // Keyboard shortcut: Ctrl+` or ` to focus terminal
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey && e.key === '`') || (e.key === '`' && !e.ctrlKey && !e.altKey && !e.metaKey)) {
                e.preventDefault();
                terminalInput.focus();
            }
        });

        // Animate orb on load
        setTimeout(() => orb.classList.add('active'), 500);

        // Initial focus
        terminalInput.focus();
    }

    function handleKeydown(e) {
        if (isProcessing) return;

        switch (e.key) {
            case 'Enter':
                e.preventDefault();
                const cmd = terminalInput.value.trim();
                if (cmd) {
                    executeCommand(cmd);
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                navigateHistory(-1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                navigateHistory(1);
                break;
            case 'Tab':
                e.preventDefault();
                autocomplete();
                break;
        }
    }

    function handleInput(e) {
        typedCommand.textContent = e.target.value;
    }

    function navigateHistory(direction) {
        if (history.length === 0) return;

        historyIndex += direction;
        if (historyIndex < 0) historyIndex = 0;
        if (historyIndex >= history.length) historyIndex = history.length - 1;

        terminalInput.value = history[historyIndex];
        typedCommand.textContent = history[historyIndex];
    }

    function autocomplete() {
        const input = terminalInput.value.trim().toLowerCase();
        const matches = Object.keys(commands).filter(cmd => cmd.startsWith(input));

        if (matches.length === 1) {
            terminalInput.value = matches[0] + ' ';
            typedCommand.textContent = matches[0] + ' ';
        } else if (matches.length > 1) {
            appendOutput(`<span class="hint">Available: ${matches.map(m => `<span class="cmd">${m}</span>`).join(', ')}</span>`);
        }
    }

    function executeCommand(input) {
        isProcessing = true;
        terminalInput.disabled = true;

        // Add to history
        history.push(input);
        historyIndex = history.length;

        // Show command
        appendOutput(`<div class="terminal-line"><span class="prompt">sir@jarvis:~$</span> <span class="command">${escapeHtml(input)}</span></div>`, false);

        // Clear input
        terminalInput.value = '';
        typedCommand.textContent = '';

        // Simulate processing delay
        setTimeout(() => {
            const [cmd, ...args] = input.toLowerCase().split(' ');
            const command = commands[cmd];

            if (command) {
                const result = command.exec(args.join(' '));
                if (result !== '__CLEAR__') {
                    appendOutput(result);
                } else {
                    clearTerminal();
                }
            } else if (cmd === '') {
                // Empty command, do nothing
            } else {
                appendOutput(`<span class="error">Command not found: <span class="cmd">${escapeHtml(cmd)}</span>. Type <span class="cmd">help</span> for available commands.</span>`);
            }

            isProcessing = false;
            terminalInput.disabled = false;
            terminalInput.focus();
            scrollToBottom();
        }, 300 + Math.random() * 400);
    }

    function appendOutput(html, scroll = true) {
        const line = document.createElement('div');
        line.className = 'terminal-line output';
        line.innerHTML = html;
        terminalBody.insertBefore(line, terminalBody.lastElementChild);
        if (scroll) scrollToBottom();
    }

    function clearTerminal() {
        const lines = terminalBody.querySelectorAll('.terminal-line:not(:last-child)');
        lines.forEach(line => line.remove());
        terminalOutput.textContent = 'Terminal cleared.';
    }

    function scrollToBottom() {
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Demo commands from hints
    document.querySelectorAll('.demo-hints kbd').forEach(kbd => {
        kbd.style.cursor = 'pointer';
        kbd.addEventListener('click', () => {
            terminalInput.value = kbd.textContent;
            typedCommand.textContent = kbd.textContent;
            terminalInput.focus();
        });
    });

    // Initialize when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for console debugging
    window.JARVIS = {
        executeCommand,
        commands,
        clearTerminal,
        history: () => history
    };
})();

// Smooth scroll for nav links
document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card, .demo-section, .contact').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Parallax effect for hero orb
document.addEventListener('mousemove', (e) => {
    const orb = document.getElementById('orb');
    if (!orb) return;

    const rect = orb.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = (e.clientX - centerX) * 0.02;
    const deltaY = (e.clientY - centerY) * 0.02;

    orb.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
});

// Orb click ripple effect
document.getElementById('orb')?.addEventListener('click', function(e) {
    const ripple = document.createElement('div');
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(0, 212, 255, 0.4);
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
        left: 50%;
        top: 50%;
        width: 100px;
        height: 100px;
        margin-left: -50px;
        margin-top: -50px;
    `;
    this.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

// Add ripple animation dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(3);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Keyboard shortcut hint
let hasShownHint = false;
document.addEventListener('keydown', (e) => {
    if (!hasShownHint && (e.ctrlKey || e.metaKey) && e.key === '`') {
        hasShownHint = true;
        const terminal = document.getElementById('terminal');
        terminal.style.boxShadow = '0 0 0 2px var(--accent), 0 0 40px var(--accent-glow)';
        setTimeout(() => {
            terminal.style.boxShadow = '';
        }, 2000);
    }
});