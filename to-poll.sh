#!/bin/bash
SERVER="http://pollingdev.sherwin.com/polling" #Default to dev

N=`tput sgr0`
B=`tput bold`
BG=`tput smso`
AFLAG=false
FFLAG=false
SFLAG=false
UFLAG=false
PFLAG=false
BATCH="deferred"
declare -a APPS=("IDN" "UPD" "PhoenixC" "CUPN" "STORE" "PARAM" "Volume" "XCDS" "APPS" "QCDS" "DXGROUP" "EDIACCT" "EDIACCT" "Cust" "MSAVEND" "SizeCodeMaintenance" "MfgMaintenance" "Cust" "PRICE-1.0" "PRICE-2.0" "ProductMaintenance" "storeStaffing" "SYSCTL" "TinterVersion" "DNRETURN")

contains (){
  local e
  for e in "${@:2}"; do [[ "$e" == "$1" ]] && return 0; done
  return 1
}

usage ()
{
  echo -e \\n"Usage Documentation for ${B}$0.${N}"
  echo -e "${B}The following command line switches indicate the environment${N}"
  echo "${BG}-p${N}  --Sets Production"
  echo "${BG}-q${N}  --Sets QA"
  echo "${BG}-d${N}  --Sets Development *Default"
  echo -e "${B}Required parameters${N}"
  echo "${BG}-a${N}  --Sets the application name"
  echo "${BG}-f${N}  --Sets the file name.  Repeatable for multiple files"
  echo "${BG}-s${N}  --Sets the store list, comma delimited or filename with comma delimted"
  echo "${BG}-U${N}  --Username for authentication"
  echo "${BG}-P${N}  --Password for authentication"

  echo -e "${B}Optional parameters${N}"
  echo "${BG}-x${N}  --Expires, integer, number of days from today"
  echo "${BG}-t${N}  --Run After Date, date format YYYY-MM-DD."
  echo "${BG}-r${N}  --Prerequisite"
  echo "${BG}-e${N}  --Request to fix works with Fix Option"
  echo "${BG}-o${N}  --Fix Option: rescind, replace, prereq, equivalent_to"
  echo "------------------------------------------------------------------"
  echo "-help  --Displays this help                                          "
  echo "Example : ${B}$0 -q -a SYSCTL -f updt-sysctl.xml -s 9959,9953 -U myuser -P mypass${N}" 1>&2
}


if [ "$#" -eq 0 ]
then
  usage
fi

while getopts ":dqpa:f:s:h:x:t:r:e:o:U:P:" opt; do
  case $opt in 
    d) 
      SERVER="https://pollingdev.sherwin.com/polling"
      ;;
    q)
      SERVER="https://pollingqa.sherwin.com/polling"
      ;;
    p) 
      SERVER="https://polling.sherwin.com/polling"
      ;;
    a) 
      AFLAG=true;APP_NM=${OPTARG}
      ;;
    f)
      FFLAG=true;FILE_NM+=(${OPTARG})
      ;;
    s)
      SFLAG=true;STORES=${OPTARG}
      ;;
    x)
      EXPIRES=${OPTARG}
      ;;
    t)
      AFTERDATE=${OPTARG}
      ;;
    r)
      PREREQ=${OPTARG}
      ;;
    e)
      REQTOFIX=${OPTARG}
      ;;
    o)
      FIXOPTION=${OPTARG}
      ;;
    U)
      UFLAG=true;API_USER=${OPTARG}
      ;;
    P)
      PFLAG=true;API_PASS=${OPTARG}
      ;;
    h)
      usage
      ;;
    \?)
      echo -e \\n"Option -${B}$OPTARG${N} not allowed"
      echo
      echo usage
      ;;
     :) 
      echo "Missing option argument for -${B}$OPTARG${N}"
      exit 2
      ;;
   esac
done 
shift $(( OPTIND -1 ))

if [[ -f $STORES ]]; then
   #This is a file to read in for data
   STORES=$(<$STORES)
fi


#apply string formatting for store list.
STORES=$(echo $STORES | sed -e 's/^/"/' -e 's/$/"/' -e 's/,/","/g')

#Validate the application name
contains "$APP_NM" "${APPS[@]}"
if [ "$?" -eq "1" ]; then
  echo "Invalid App: ${B}$APP_NM${N}"
  echo "Valid Apps are:"
  echo ${B}${APPS[@]}${N}
  exit
fi

#Validate require parms were set
if ! $AFLAG; then
   echo "Require parameter ${B}-a${N} missing"
   exit
fi

if $FFLAG; then
  if ! [[ -f $FILE_NM ]]; then
   echo "Invalid file name ${B}$FILE_NM${N}"
   exit
fi

fi

 
if ! $SFLAG; then 
   echo "Required parameter ${B}-s${N} missing"
   exit
fi

if ! $UFLAG; then
   echo "Required parameter ${B}-U${N} missing"
   exit
fi

if ! $PFLAG; then
   echo "Required parameter ${B}-P${N} missing"
   exit
fi




echo ""
echo "Sending requests for"
echo "____________________"
echo "${BG}Server:${N} $SERVER"
echo "${BG}App:${N} $APP_NM"
for FILE in "${FILE_NM[@]}"; do
    echo "${BG}File:${N} $FILE"
done
echo "${BG}Stores:${N} $STORES"
echo "${BG}Prereq:${N} $PREREQ"
echo "${BG}Expires:${N} $EXPIRES"
echo "${BG}Run After:${N} $AFTERDATE"
echo "${BG}Fix Option:${N} $FIXOPTION"
echo "${BG}Req to Fix:${N} $REQTOFIX"
echo ""

read -p "Are you sure? "
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
  echo""
  exit 2
fi
echo ""
USER="--user ${API_USER}:${API_PASS} -k"

# ── Output helpers ─────────────────────────────────────────────────────────
CURL_STATUS=""
CURL_BODY=""

do_curl() {
  local TMPFILE
  TMPFILE=$(mktemp)
  CURL_STATUS=$(curl $USER -s -o "$TMPFILE" -w "%{http_code}" "$@")
  CURL_BODY=$(cat "$TMPFILE")
  rm -f "$TMPFILE"
}

ok()   { echo "  ${B}[OK]${N}   $*"; }
fail() { echo "  ${B}[FAIL]${N} $*" >&2; }
warn() { echo "  ${B}[WARN]${N} $*"; }
step() { echo ""; echo "${BG} Step $1: $2 ${N}"; }

print_response() {
  local body="$1"
  if [ -z "$body" ]; then
    echo "  (empty response)" >&2
    return
  fi
  # Surface the message field first if present
  local msg
  msg=$(echo "$body" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
  [ -n "$msg" ] && echo "  ${B}Message:${N} $msg" >&2
  # Pretty-print JSON; fall back to stripping HTML tags
  echo "  ────────────────────────────────" >&2
  local pretty
  pretty=$(echo "$body" | python3 -m json.tool 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "$pretty" | sed 's/^/  /' >&2
  else
    echo "$body" | sed 's/<[^>]*>//g' | sed '/^[[:space:]]*$/d' | sed 's/^/  /' >&2
  fi
  echo "  ────────────────────────────────" >&2
}

PARMS="{"

if [ ${PREREQ} ]; then
  if [ ${PARMS} != "{" ]; then
     PARMS="${PARMS},"
  fi
  PARMS="${PARMS}\"afterSequence\":\"${PREREQ}\"" 
fi

if [ ${EXPIRES} \] ; then
  if [ ${PARMS} != "{" ]; then
     PARMS="${PARMS},"
  fi
  PARMS="${PARMS}\"expiration\":\"${EXPIRES}\""
fi

if [ ${AFTERDATE} \] ; then
  if [ ${PARMS} != "{" ]; then
     PARMS="${PARMS},"
  fi
  PARMS="${PARMS}\"afterDate\":\"${AFTERDATE}\""
fi

if [ ${REQTOFIX} \] ; then
  if [ ${PARMS} != "{" ]; then
     PARMS="${PARMS},"
  fi
  PARMS="${PARMS}\"fixRequestId\":\"${REQTOFIX}\""
fi

if [ ${FIXOPTION} \] ; then
  if [ ${PARMS} != "{" ]; then
     PARMS="${PARMS},"
  fi
  PARMS="${PARMS}\"fixOption\":\"${FIXOPTION}\""
fi

PARMS="${PARMS}}"


# ── Step 1: Create request ─────────────────────────────────────────────────
STRING="${SERVER}/v1/app/${APP_NM}"
step 1 "Creating request"
echo "  POST $STRING"

do_curl -X POST -H "Accept: application/json" "$STRING"

if [ "$CURL_STATUS" != "201" ] && [ "$CURL_STATUS" != "200" ]; then
  fail "Failed to create request.  HTTP $CURL_STATUS"
  print_response "$CURL_BODY"
  exit 1
fi

REQID=$(echo "$CURL_BODY" | grep -o '"requestId":"[^"]*"' | cut -d'"' -f4)

if [ -z "$REQID" ]; then
  fail "Could not extract requestId from response.  HTTP $CURL_STATUS"
  print_response "$CURL_BODY"
  exit 1
fi

ok "Request created.  ID: ${B}$REQID${N}"

BASESTRING="${SERVER}/v1/${REQID}"
OPS="${BASESTRING}/operations"
STR="${BASESTRING}/stores"

# ── Step 2: Apply optional parameters ─────────────────────────────────────
if [ "$PARMS" != "{}" ]; then
  step 2 "Applying request parameters"
  echo "  PUT $BASESTRING"
  echo "  Params: $PARMS"

  do_curl -X PUT \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -d "$PARMS" "$BASESTRING"

  if [ "$CURL_STATUS" != "200" ]; then
    fail "Failed to apply parameters.  HTTP $CURL_STATUS"
    print_response "$CURL_BODY"
    exit 1
  fi
  ok "Parameters applied."
fi

# ── Step 3: Upload file operations ─────────────────────────────────────────
step 3 "Uploading file operations"
for FILE in "${FILE_NM[@]}"; do
  FN=$(basename "$FILE")
  MD5=$(shasum "$FILE" | sed 's/ .*$//g')
  echo "  POST $OPS"
  echo "  File: $FILE  Checksum: $MD5"

  do_curl -X POST -H "Accept: application/json" \
    -F "blob=@$FILE" -F "filename=$FN" -F "checksum=$MD5" \
    -F "algorithm=SHA-1" -F "transforms=null" "$OPS"

  if [ "$CURL_STATUS" != "201" ]; then
    fail "Failed to upload $FN.  HTTP $CURL_STATUS"
    print_response "$CURL_BODY"
    exit 1
  fi
  ok "Uploaded: $FN"
done

# ── Step 4: Set target stores ──────────────────────────────────────────────
step 4 "Setting target stores"
if [ "$STORES" == "\"all\"" ]; then
  TYPE="chain"
else
  TYPE="store"
fi
echo "  PUT $STR"
echo "  Type: $TYPE  Stores: $STORES"

do_curl -X PUT \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"$TYPE\",\"data\":[${STORES}]}" "$STR"

if [ "$CURL_STATUS" != "201" ]; then
  fail "Failed to set stores.  HTTP $CURL_STATUS"
  print_response "$CURL_BODY"
  exit 1
fi
ok "Stores set."

# ── Step 5: Submit request ─────────────────────────────────────────────────
step 5 "Submitting request"
echo "  POST $BASESTRING"

do_curl -X POST -H "Accept: application/json" "$BASESTRING"

if [ "$CURL_STATUS" == "206" ]; then
  warn "Submitted, but not all stores accepted.  HTTP 206"
elif [ "$CURL_STATUS" != "200" ]; then
  fail "Failed to submit request.  HTTP $CURL_STATUS"
  print_response "$CURL_BODY"
  exit 1
else
  ok "Request submitted successfully."
fi

echo ""
echo "${BG} Done ${N}  Request ID: ${B}$REQID${N} submitted to $SERVER"
echo ""

