#!/bin/bash

PORT=8005
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function check_status() {
    if pgrep -f "uvicorn main:app.*$PORT" > /dev/null; then
        echo "워크샵 서버가 실행 중입니다. (포트: $PORT)"
        return 0
    else
        echo "워크샵 서버가 실행되지 않았습니다."
        return 1
    fi
}

function start_server() {
    if check_status > /dev/null; then
        echo "서버가 이미 실행 중입니다."
    else
        echo "워크샵 서버를 시작합니다..."
        cd "$APP_DIR"
        nohup uvicorn main:app --host 0.0.0.0 --port $PORT > workshop.log 2>&1 &
        sleep 2
        if check_status > /dev/null; then
            echo "서버가 성공적으로 시작되었습니다."
        else
            echo "서버 시작에 실패했습니다. workshop.log를 확인해주세요."
        fi
    fi
}

function stop_server() {
    if pkill -f "uvicorn main:app.*$PORT"; then
        echo "워크샵 서버를 중지했습니다."
    else
        echo "실행 중인 서버가 없습니다."
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        check_status
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0 