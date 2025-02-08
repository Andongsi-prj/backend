$(document).ready(function () {

    const BELT = $(".belt");
    
    // 파이프 검사 설정
    const SETTINGS = {
        beltSpeed: 20,
        loadInterval: 10000,
        startPosition: -800
    };

    // 이미지 처리 설정 & 로그 설정
    const processedImages = new Set();
    const LOG_SETTINGS = {
        maxLogItems: 3,
        logContainer: '#log-list'
    };
    




    // 이미지 로드 & 애니메이션
    function loadAndAnimateImage() {
        fetch('/api/images/images', {
            method: 'POST',
            headers: {'Content-Type': 'application/json',}
        })
        .then(res => res.ok ? res.json() : Promise.reject('HTTP 오류'))
        .then(data => {
            if (data.status === 'success' && !processedImages.has(data.plt_number)) {
                const $img = $(`<img src="${data.image}" />`);
                $img.data('plt_number', data.plt_number);
                BELT.append($img);
                animateImage($img);
                processedImages.add(data.plt_number);
                
                setTimeout(() => {
                    processedImages.delete(data.plt_number);
                }, SETTINGS.beltSpeed * 1000 * 2);
            }
        })
        .catch(err => setTimeout(loadAndAnimateImage, 7000));
    }


    
    // 이미지 애니메이션
    function animateImage($img) {
        $img.on('load', function() {
            $(this).css({
                position: "absolute",
                transform: `translateX(${SETTINGS.startPosition}px)`,
                transition: `transform ${SETTINGS.beltSpeed}s linear`
            });
            
            requestAnimationFrame(() => {
                $(this).css("transform", `translateX(${window.innerWidth + 100}px)`);
            });
        });
    }



    // 이미지 검출 영역 탐지
    function detectPosition() {
        const detectionZone = document.querySelector('.detection-zone');
        const zoneLeft = detectionZone.getBoundingClientRect().left;
        const zoneRight = detectionZone.getBoundingClientRect().right;
    
        requestAnimationFrame(() => {
            $('.belt img').each(function () {
                const $img = $(this);
                const imgRect = this.getBoundingClientRect();
    
                if (imgRect.left <= zoneRight && imgRect.right >= zoneLeft && !$img.data('processed')) {
                    processImage($img);
                    $img.data('processed', true);
                }
    
                if (imgRect.left > zoneRight && $img.data('processed')) {
                    setTimeout(() => {
                        $img.fadeOut(1000, function() {
                            $(this).remove();
                        });
                    }, 2000);
                }
            });
            detectPosition();
        });
    }


    // 로그 추가
    async function addLog(type, message, pltNumber) {
        // UI에 로그 추가
        const logItem = document.createElement('li');
        logItem.className = type === 'warning' ? 'defect' : '';
        logItem.innerHTML = `
            <span class="log-time">[${new Date().toLocaleString('ko-KR')}]</span>
            <span class="log-plt">[PLT: ${pltNumber}]</span>
            ${message}
        `;

        const logList = document.getElementById('log-list');
        logList.insertBefore(logItem, logList.firstChild);

        while (logList.children.length > LOG_SETTINGS.maxLogItems) {
            logList.removeChild(logList.lastChild);
        }

        // Kafka로 로그 전송
        try {
            await fetch('/api/logs/logs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    message: message,
                    pltNumber: pltNumber,
                    
                })
            });
        } catch (error) {
            console.error('Kafka 로그 전송 실패:', error);
        }
    }
    


    // 이미지 처리
    async function processImage($img) {
        const pltNumber = $img.data('plt_number');
        try {
            $img.addClass('processing');
            const res = await fetch('/api/pipe/pipe', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    image_base64: $img.attr('src').split('base64,')[1],
                    plt_number: pltNumber
                }),
            });

            const result = await res.json();
            
            // Kafka로 원본 이미지만 전송
            await fetch('/api/logs/kafka-ig', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    message: '이미지 데이터',
                    pltNumber: pltNumber,
                    image: $img.attr('src').split('base64,')[1]
                })
            });
            
            requestAnimationFrame(() => {
                $img.attr('src', `data:image/png;base64,${result.annotated_image}`)
                    .removeClass('processing');

                if (result.predictions.some(p => p.label === 'Defect')) {
                    addLog('warning', '불량품', pltNumber);
                    Swal.fire({
                        icon: "warning",
                        title: "불량품 감지!",
                        text: `파이프 번호: ${pltNumber}`,
                        confirmButtonText: "확인",
                        timer: 2000,
                        timerProgressBar: true,
                        customClass: {timerProgressBar: "timer-bar"}
                    });
                } else {
                    addLog('info', '정상품', pltNumber);
                }
            });
        } catch (error) {
            addLog('error', `검사 실패`, pltNumber);
            $img.removeClass('processing');
        }
    }

    loadAndAnimateImage();
    setInterval(loadAndAnimateImage, SETTINGS.loadInterval);
    detectPosition();
});

