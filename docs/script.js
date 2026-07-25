document.addEventListener('DOMContentLoaded', () => {
    // Nav Scroll logic
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-links a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });

    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId.startsWith('#')) {
                e.preventDefault();
                const targetSection = document.querySelector(targetId);
                if (targetSection) {
                    window.scrollTo({
                        top: targetSection.offsetTop - 50,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Scroll Animations (Intersection Observer)
    const fadeElements = document.querySelectorAll('[data-animate="fade-up"]');

    const fadeObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Apply delay if specified
                const delay = entry.target.getAttribute('data-delay');
                if (delay) {
                    entry.target.style.transitionDelay = delay;
                }
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    fadeElements.forEach(el => fadeObserver.observe(el));

    // Counter Animations
    const counters = document.querySelectorAll('.stat-number');
    let counted = false;

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !counted) {
                counters.forEach(counter => {
                    const updateCount = () => {
                        const target = +counter.getAttribute('data-target');
                        const count = +counter.innerText;
                        const inc = target / 50; // speed

                        if (count < target) {
                            counter.innerText = Math.ceil(count + inc);
                            setTimeout(updateCount, 30);
                        } else {
                            // Add commas for large numbers
                            counter.innerText = target.toLocaleString();
                        }
                    };
                    updateCount();
                });
                counted = true;
            }
        });
    }, { threshold: 0.5 });

    const statsSection = document.querySelector('#stats');
    if (statsSection) {
        counterObserver.observe(statsSection);
    }

    // Interactive Tabs Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active classes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });

    // Image Modal Logic (applies to gallery and interactive tab images)
    const modal = document.getElementById("image-modal");
    const modalImg = document.getElementById("modal-img");
    const captionText = document.getElementById("modal-caption");
    const closeBtn = document.querySelector(".close-modal");
    const interactiveImages = document.querySelectorAll('.gallery-item img, .interactive-img');

    interactiveImages.forEach(img => {
        img.addEventListener('click', function () {
            modal.style.display = "block";
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
            modalImg.src = this.src;
            captionText.innerHTML = this.alt;
        });
    });

    const closeModal = () => {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = "none";
        }, 300);
    };

    closeBtn.addEventListener('click', closeModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape" && modal.classList.contains('show')) {
            closeModal();
        }
    });

    // Magnetic Button Effect
    const magneticBtns = document.querySelectorAll('.magnetic');

    magneticBtns.forEach(btn => {
        btn.addEventListener('mousemove', function (e) {
            const position = btn.getBoundingClientRect();
            // Use clientX/Y so it's relative to the viewport like getBoundingClientRect
            const x = e.clientX - position.left - position.width / 2;
            const y = e.clientY - position.top - position.height / 2;

            btn.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
        });

        btn.addEventListener('mouseleave', function (e) {
            btn.style.transform = `translate(0px, 0px)`;
        });
    });

    // Fetch latest release from GitHub API
    const fetchLatestRelease = async () => {
        try {
            const response = await fetch('https://api.github.com/repos/dipta-roy/PlanIFlow/releases/latest');
            if (response.ok) {
                const data = await response.json();
                const version = data.tag_name;
                const publishedAt = new Date(data.published_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });

                const versionSpan = document.getElementById('latest-version-text');
                const dateP = document.getElementById('latest-release-date');
                const downloadBtn = document.getElementById('latest-download-btn');

                if (versionSpan) versionSpan.textContent = `(${version})`;
                if (dateP) dateP.textContent = `Released on ${publishedAt}`;

                // If there's an MSI asset, use that link directly instead of the generic latest page
                const msiAsset = data.assets.find(asset => asset.name.endsWith('.msi'));
                if (msiAsset && downloadBtn) {
                    downloadBtn.href = msiAsset.browser_download_url;
                }
            }
        } catch (error) {
            console.error('Failed to fetch latest release:', error);
        }
    };
    fetchLatestRelease();
});
