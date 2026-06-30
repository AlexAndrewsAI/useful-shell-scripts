
alias psfind="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/psfind.sh"
alias pskill="psfind -k"

# Repeat a command at a specified interval
# Usage: repeat [-dt <seconds>] <command>
repeat() {

    # Default values
    command=""
    dt=1
    # Process command line arguments
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            -dt)
                dt="$2"
                shift 2  # Move past the flag and its argument
                ;;
            *)
                command="$command $1"  # Append other arguments to command
                shift  # Move past the current argument
                ;;
        esac
    done

    # Trim leading/trailing whitespace from command
    command=$(echo "$command" | xargs)

    # Check if the command or alias is found
    if ! type "$command" &> /dev/null; then
        if alias | grep -q "^alias $command="; then
            echo "Alias '$command' found."
        else
            echo "Error: Command or Alias '$command' not found."
            exit 1
        fi
    fi

    while true; do
        echo "Running command: eval \"$command\""
        eval "$command"
        sleep "$dt"
    done

}

alias pskill-headless="pskill headless"
alias headless-pskill="pskill-headless"

# Nice (lower priority) processes matching a search term
# Usage: psnice <search_term>
psnice() {
    term=$1
    for ps in $(psfind "$term" | awk '{print $1}'); do
        echo "renice -n 19 -p $ps"
        renice -n 19 -p "$ps"
    done
}
alias run-limits="systemd-run --scope -p MemoryLimit=20000M -p CPUQuota=85% --property=Delegate=yes"




# Toggle run state between SIGSTOP (similar to ctrl-Z in terminal) and SIGCONT
# Toggle only USER's highest CPU job. If paused, it saves it to a file to resume
# Usage: pstoggle [PID_or_name]
pstoggle() {
    PID=$1
    # Check if PID is all digits
    if [[ $PID =~ ^[0-9]+$ ]]; then
        echo "Running $PID"
    else
        echo "Trying to find $PID"
        PID=$(psfind "$PID" | head -1 | awk '{print $1}')
    fi

    fout="$LOGDIR/.pstoggle.pid"
    # If none specified get highest cpu process
    if [[ "$PID" == "" ]]; then
        # Read PID if file exists and toggle that process
        if [[ -f "$fout" ]]; then
            echo "Reading PID from $fout"
            read -r PID < "$fout"
            # If PID still exists, resume it
            echo "Existing stopped process $PID found. Resuming."
            rm -f "$fout"
            ps "$PID"
            kill -SIGCONT "$PID"
            return 1
        else
            # PID=$(ps -eo pid,%cpu --sort=-%cpu | head -n 2 | tail -n 1 | awk '{print $1}')
            PID=$(top -b -n 1 | grep " $USER " | head -1 | awk '{print $1}')
            echo "No PID specified, using highest CPU process with PID $PID."
        fi
    fi
    ps "$PID"
    echo "Toggling $PID"
    if ps -o stat= -p "$PID" | grep -q 'T'; then
        # Process is stopped, send SIGCONT
        kill -SIGCONT "$PID"
        echo "Process $PID resumed."
        rm -f "$fout"
    else
        # Process is running, send SIGSTOP
        kill -SIGSTOP "$PID"
        echo "Process $PID stopped."
        echo "$PID" > "$fout"
    fi
}


# Kill processes exceeding CPU threshold with specified signal
# First argument is threshold CPU usage, rest are additional arguments for kill
# Usage: process-kill-threshhold [threshold] [kill_args...]
# Example: process-kill-threshhold 120 -SIGSTOP
process-kill-threshhold() {
    # From stackoverflow, Marcel Kohls https://stackoverflow.com/questions/187804/automatically-kill-process-that-consume-too-much-memory-or-stall-on-linux
    if [ -z "$1" ]
    then
        maxlimit=110
    else
    maxlimit=$1
    fi

    shift  # This removes the first argument from the list
    remaining_args=("$@")  # Store the remaining arguments in an array

    ps axo user,%cpu,pid,vsz,rss,uid,gid --sort %cpu,rss\
    | awk -v max="$maxlimit" '$6 != 0 && $7 != 0 && $2 > max'\
    | awk '{print $3}'\
    | while read -r line;\
        do\
        ps u --no-headers -p "$line";\
        echo "$(date) - $(ps u --no-headers -p "$line")" >> pkill.log;\
        notify-send 'Killing process!' "${remaining_args[*]}" "$(ps -p "$line" -o command --no-headers | awk '{print $1}')" -u normal -i dialog-warning -t 3000;\
        kill "$line" "${remaining_args[@]}";\
    done;
}

# Run command with nice priority in background
# Usage: nnice [-f] <command> [args...]
# -f flag saves command to .nnice-input.bash for batch execution
nnice() {
        echo "$*"
        if [[ "$1" == "-f" ]]; then
                shift
                echo "$*" >> .nnice-input.bash
                nohup nice -10 bash .nnice-input.bash &
        else
                nohup nice -10 "$@" &
        fi
        #nohup nice -10 "$@" &
}

# Run command with nohup, output to timestamped file
# First line of output is PID
# Usage: nohup-date <command> [args...]
nohup-date() {
    # Runs a command nohup output to timestamped file
    # First line of output is PID
    if [ "$#" -eq 0 ]; then
        echo "Usage: nohup-date <command>"
    else
        dtime="$(date +%Y-%m-%d_%H-%M-%S)"
        outfile="nohup-$dtime"
        nohup sleep 1; "$@" >> "$outfile.out" 2>&1 &
        pid=$!
        echo "$pid" >> "$outfile.out"
    fi
}
