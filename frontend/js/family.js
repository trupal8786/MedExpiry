<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Family Sharing — MedExpiry</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/custom.css">
    <script>
        tailwind.config = {
            theme: { extend: { fontFamily: { sans:['Inter','sans-serif'], display:['Space Grotesk','sans-serif'] }, colors: { brand:{400:'#4ade80',500:'#22c55e',600:'#16a34a'}, dark:{800:'#1e1e2e',900:'#11111b',950:'#0a0a14'} } } } }
    </script>
</head>
<body class="bg-dark-950 text-white min-h-screen font-sans">

    <!-- NAV -->
    <nav class="fixed top-0 w-full z-50 bg-dark-950/80 backdrop-blur-xl border-b border-white/5">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <a href="index.html" class="flex items-center gap-3">
                    <div class="w-9 h-9 bg-gradient-to-br from-brand-400 to-brand-600 rounded-xl flex items-center justify-center">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                    </div>
                    <span class="text-xl font-display font-bold">Med<span class="text-brand-400">Expiry</span></span>
                </a>
                <div class="hidden md:flex items-center gap-1">
                    <a href="index.html" class="nav-link">Dashboard</a>
                    <a href="scan.html" class="nav-link">Scan</a>
                    <a href="track.html" class="nav-link">Track</a>
                    <a href="donate.html" class="nav-link">Donate</a>
                    <a href="family.html" class="nav-link active">Family</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- FAMILY PAGE -->
    <section class="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
        <div class="mb-8">
            <h1 class="text-3xl font-display font-bold mb-2">Family Sharing</h1>
            <p class="text-gray-400">Share your medicine inventory with family members. Everyone stays informed about expiry dates.</p>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
            <!-- Create Family -->
            <div class="bg-dark-800/30 rounded-3xl border border-white/5 p-6">
                <h2 class="font-display font-bold text-lg mb-4 flex items-center gap-2">👨‍👩‍👧‍👦 Create Family Group</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1.5">Family Name</label>
                        <input type="text" id="familyName" placeholder="e.g., Sharma Family" class="w-full px-4 py-3 bg-dark-900 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50 transition-colors">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1.5">Your Name</label>
                        <input type="text" id="creatorName" placeholder="e.g., Rahul" class="w-full px-4 py-3 bg-dark-900 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50 transition-colors">
                    </div>
                    <button onclick="createFamily()" class="w-full py-3 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-xl transition-all">
                        Create Family Group
                    </button>
                </div>
                <div id="createResult" class="mt-4 hidden"></div>
            </div>

            <!-- Join Family -->
            <div class="bg-dark-800/30 rounded-3xl border border-white/5 p-6">
                <h2 class="font-display font-bold text-lg mb-4 flex items-center gap-2">🔗 Join Existing Family</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1.5">Invite Code</label>
                        <input type="text" id="inviteCode" placeholder="e.g., A3B7C1" maxlength="6" class="w-full px-4 py-3 bg-dark-900 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50 transition-colors uppercase tracking-widest text-center text-xl font-display">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1.5">Your Name</label>
                        <input type="text" id="memberName" placeholder="e.g., Priya" class="w-full px-4 py-3 bg-dark-900 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50 transition-colors">
                    </div>
                    <button onclick="joinFamily()" class="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-xl border border-white/10 transition-all">
                        Join Family
                    </button>
                </div>
                <div id="joinResult" class="mt-4 hidden"></div>
            </div>
        </div>

        <!-- Info Section -->
        <div class="mt-8 bg-brand-500/5 border border-brand-500/10 rounded-2xl p-6">
            <h3 class="font-display font-bold mb-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                How Family Sharing Works
            </h3>
            <div class="text-sm text-gray-400 space-y-2">
                <p>1. Create a family group and get a unique 6-character invite code.</p>
                <p>2. Share the code with family members — they can join from their device.</p>
                <p>3. All members see the shared medicine inventory and get expiry alerts.</p>
                <p>4. Great for elderly parents living separately — you'll get notified about their expiring medicines too.</p>
            </div>
        </div>
    </section>

    <script src="js/family.js"></script>
</body>
</html>
