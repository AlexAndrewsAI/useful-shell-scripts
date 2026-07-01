# Set DIR_VENV from config file
if [ "$(command -v yq)" ] && [ -n "$FILE_BASHRC_CONFIG" ] && [ -f "$FILE_BASHRC_CONFIG" ]; then
    # Check if venv is configured as an object with location field
    venv_location=$(yq '.venv.location' "$FILE_BASHRC_CONFIG" 2>/dev/null)
    if [[ -n "$venv_location" && "$venv_location" != "null" ]]; then
        # Strip leading and trailing double quotes
        venv_location="${venv_location#\"}"
        venv_location="${venv_location%\"}"
        
        # Resolve venv path relative to config file directory
        config_dir=$(dirname "$FILE_BASHRC_CONFIG")
        if [[ "$venv_location" != /* ]]; then
            venv_path="$config_dir/$venv_location"
        else
            venv_path="$venv_location"
        fi
        
        # Export the venv path
        export DIR_VENV="$venv_path"
    fi
fi

if [ "$(command -v uv)" ]; then
    # Run complete test suite with coverage and formatting
    # Uses current directory name as project name (override with COV_PROJECT env var)
    # Steps: activate venv, sync dev dependencies, format, lint, test with coverage, type check
    alias uv-tests="source .venv/bin/activate; uv sync --dev; uv run ruff format; uv run ruff check --fix; uv run pytest --cov=\${COV_PROJECT:-\$(basename \$(pwd))} --cov-report term-missing; uv run mypy ."
    # Create virtual environment in current directory if missing and activate it
    alias venv-here="[ ! -d .venv ] && uv venv; source .venv/bin/activate"
    # Display the current virtual environment path
    alias venv-which="echo $VIRTUAL_ENV"
    # Deactivate the current virtual environment
    alias venv-deactivate="deactivate"
    # Activate the main venv specified in config (DIR_VENV)
    if [ -n "$DIR_VENV" ]; then
        alias venv-main="source $DIR_VENV/bin/activate"
    fi
fi

# Go to the main venv directory
if [ -n "$DIR_VENV" ]; then
    alias goto-venv-main="cd $DIR_VENV"
fi

# General
if [ "$(command -v vim)" ]; then
    alias vi="vim"
fi



# shortcut to read multiple lines into an array 'lines'
alias lines2array="echo 'readarray -t lines <<< ...' ; readarray -t lines <<<"

# Convert YAML string to bash array format
# Usage: yaml2bash <yaml_string>
# Handles arrays, objects, and scalars
if [ "$(command -v yq)" ]; then
    yaml2bash() {
        local yaml_string="$1"
        local -a output_array

        # Determine the root data type using yq's type operator
        local root_type
        root_type=$(echo "$yaml_string" | yq -r 'type')

        case "$root_type" in
            # Array (List): Save each array element into the output_array
            "array")
                while IFS= read -r item; do
                    output_array+=("$item")
                done < <(echo "$yaml_string" | yq -r '.[]')
                ;;

            # Object (Dictionary): Save key-value pairs as Bash-friendly assignment strings
            "object")
                while IFS= read -r entry; do
                    output_array+=("$entry")
                done < <(echo "$yaml_string" | yq -r 'to_entries | .[] | .key + "=\"" + .value + "\""' )
                ;;

            # String/Number/Boolean (Scalar): Assign the raw scalar value to the output_array
            "string"|"number"|"boolean")
                output_array=("$yaml_string")
                ;;

            *)
                echo "Error: Unhandled YAML type or empty input: $root_type" >&2
                return 1
                ;;
        esac

        # Output the array (formatted for Bash)
        printf '%s\n' "${output_array[@]}"
    }
fi

#region Git utilities
if [ "$(command -v git)" ]; then
    alias git-diff="git diff --name-only | cat"
    alias git-tree-files="git ls-tree -r --name-only HEAD | tree -a --fromfile"
    alias git-current-branch="git rev-parse --abbrev-ref HEAD"
    alias git-merge-dry-run="git merge --no-commit --no-ff"

    # Stage all changes and commit with timestamp message
    # Usage: git-update
    git-update() {
        git add .
        git commit -m "update-$(datetime)"
    }

    # Pull all remote branches and return to current branch
    # Usage: git-pull-all-branches
    git-pull-all-branches() {
        current_branch=$(git branch --show-current)
        for branch in $(git branch -r | grep -v '\->'); do
            git checkout --track $branch || git checkout ${branch#origin/} && git pull
        done
        git checkout $current_branch
    }


    # Unzip a single zip file in current directory, replace git files, and optionally commit
    # Usage: git-unzip-update
    # Environment variable: GIT_AUTO_COMMIT (set to "yes" to auto-commit without prompt)
    git-unzip-update() {
        if [ $(ls -1 *.zip 2>/dev/null | wc -l) -eq 1 ]; then
            for f in `git ls-files`; do
                # Skip files that start with .git
                if [[ "$f" == ".git"* ]]; then
                    echo "Skipping git file: $f"
                    continue
                fi
                rm $f
            done
            z=$(ls -1 *.zip | head -1)
            # Unzip the file
            unzip "$z"
            rm "$z"
            # Get user confirmation to add and commit
            if [ -t 0 ]; then
                read -p "Unzipped files. Do you want to add and commit them? (y/N): " CONFIRMATION
            elif [ "$GIT_AUTO_COMMIT" = "yes" ]; then
                CONFIRMATION="y"
            else
                CONFIRMATION="n"
            fi
            if [[ "$CONFIRMATION" =~ ^[yY]$ ]]; then
                echo "Adding and committing changes..."
                git add --all
                git commit -m "update-$(datetime)"
                echo "Changes committed."
            else
                echo "Add and commit cancelled."
                return 1
            fi
        else
            echo "WARNING There is not exactly 1 zip file in the current directory. Skipping."
        fi

    }

fi
#endregion git

#region Docker utilities
if [ "$(command -v docker)" ]; then
    # Delete Docker images with <none> repository, with confirmation
    # Checks for dependent containers first before deleting images
    # Usage: docker-delete-images-search
    # Environment variable: DOCKER_AUTO_DELETE (set to "yes" to auto-delete without prompts)
    docker-delete-images-search() {
        ids=$(docker images --format "{{.ID}} {{.Repository}}" | awk -v term="<none>" '$2 ~ term {print $1}')
        tosearch=""
        for i in $ids; do
            tosearch="$tosearch|$i"
        done
        echo $SEARCH $tosearch
        containers=$(docker container ls -a | grep -E "CONTAINER ID$tosearch")

        if [ $(echo -e "$containers" | wc -l) -gt 1 ]; then
            echo "================= Dependent Containers ======================"
            echo -e "$containers"
            if [ -t 0 ]; then
                read -p "Delete CONTAINERS using these images? (y/N): " CONFIRMATION
            elif [ "$DOCKER_AUTO_DELETE" = "yes" ]; then
                CONFIRMATION="y"
            else
                CONFIRMATION="n"
            fi
            if [[ "$CONFIRMATION" =~ ^[yY]$ ]]; then
                echo "Deleting containers..."
                for c in $(docker container ls -a | grep -E "$tosearch" | awk '{print $1}'); do
                    docker rm $c
                done
                echo "Deletion complete."
            else
                echo "Deletion cancelled."
                return
            fi
        fi

        echo "================= Found Images ======================"
        docker image ls | grep -E "IMAGE ID$tosearch"
        if [ -t 0 ]; then
            read -p "Are you sure you want to delete these images? (y/N): " CONFIRMATION
        elif [ "$DOCKER_AUTO_DELETE" = "yes" ]; then
            CONFIRMATION="y"
        else
            CONFIRMATION="n"
        fi

        if [[ "$CONFIRMATION" =~ ^[yY]$ ]]; then
            echo "Deleting images..."
            docker rmi $ids
            echo "Deletion complete."
            echo
        else
            echo "Deletion cancelled."
        fi

    }

    # Delete all Docker images except those with 'latest' tag
    # Usage: docker-delete-nonlatest
    docker-delete-nonlatest() {
        # Get a list of all images
        images=$(docker images --format '{{.Repository}}:{{.Tag}}')

        # Loop through each image
        for image in $images; do
            # Check if the image has the "latest" tag
            image_name=$(echo "$image" | sed 's/:.*//')
            if docker images --format '{{.Repository}}:latest' | grep -q "^${image_name}:latest\$"; then
                echo "Skipping image with latest tag: $image"
            else
                echo "Removing image: $image"
                docker rmi "$image"
            fi
        done
    }

    # Start and attach to a Docker container
    # Usage: docker-start-attach <container_id>
    docker-start-attach() {
        docker start $1
        docker attach $1
    }

fi
#endregion



#region Kubernetes utilities
if [ "$(command -v kubectl)" ]; then
    alias kubernetes-getpod="kubectl get pods"

    # Execute a command in a Kubernetes pod by name pattern
    # Usage: kubernetes-exec <pod_name_pattern>
    kubernetes-exec() {
        echo "$1"
        temp=`kubectl get pods | grep "$1" | awk '{print $1}'`
        echo "kubectl exec -it \"$temp\" bash"
        k exec -it "$temp" bash
    }

    # Delete all kubernetes resources
    alias kubernetes-delete-all="kubectl delete all --all"

    # Delete kubernetes resources matching a name pattern
    # Usage: kubernetes-delete <name_pattern>
    kubernetes-delete() {
        if [ "$1" == "" ]; then
            echo "Please provide a name to delete"
            return
        fi
        tofind=$1
        tmpfile=$(mktemp)
        kubectl get all | awk '{print $1}'  > $tmpfile
        for line in $(grep "$tofind" $tmpfile); do
            kubectl delete "$line"
        done
        rm $tmpfile
    }
    # Load all YAML files in current directory into kubernetes
    alias kubernetes-yaml-load="for f in *.yaml; do kubectl apply -f $f; done"
fi
#endregion


# Convert a string representation of an array to a bash array
# Handles Python-style list syntax and quoted values
# Usage: str2array <array_name> <string_value>
str2array() {
    key=$1
    value=$2
    local -a temp
    # Remove leading/trailing [], assuming this is python syntax
    # If you really need not this you can try "[[one], [two]]"
    if [[ "$value" == [* ]] && [[ "$value" == *] ]]; then
        # Set new variable to everything in between
        value="${value:1:-1}"  # Remove first and last character
    fi
    # Create an array from the comma-separated list
    IFS=',' read -ra temp <<< "$value"
    i=0
    for i in "${!temp[@]}"; do
        currentValue=${temp[$i]}
        # Check if the value starts and ends with single or double quotes
        if [[ "${currentValue}" =~ ^[\"'].*[\"']$ ]]; then
            # Strip both the leading and trailing quotes
            strippedValue="${currentValue:1:-1}"
            # Assign the stripped value back to the array
            temp[$i]="$strippedValue"
        fi
    done
    eval "$key=(\"\${temp[@]}\")"
}


