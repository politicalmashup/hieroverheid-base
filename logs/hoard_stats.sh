#!/usr/bin/env bash
# run this script from the project root dir

printf "Number of loaded documents per ES index:\n\n"
wc -w index-state/o*.ids
printf "\n"

# count created and updated abbr definitions per log file
LC_NUMERIC="en_US.UTF-8"
for f in logs/o*-hoards-*.log
do
  SUM_CR=$(grep '^document' "$f" | awk '{s += substr($3,2)} END {print s}')
  SUM_UP=$(awk '{s += substr($4,2)} END {print s}' "$f")
  if [[ "$SUM_CR" -gt "0" ]]; then
    PERCENT_UPDATED=$(printf "%.2f\n" "$(bc -l <<< "$SUM_UP / ($SUM_UP + $SUM_CR) * 100")" )
    echo "$f"
    echo "  $SUM_CR abbreviation definitions were new within a committee"
    echo "  $SUM_UP definitions matched a known abbreviation with a different long form"
    if [[ "$SUM_UP" -gt "0" ]]; then
      echo "  $PERCENT_UPDATED% of definitions were previously defined with a different long form"
    fi
  fi
done

# count total created and updated abbr definitions
SUM_CR=$(grep '^document' logs/o*-hoards-*.log | awk '{s += substr($3,2)} END {print s}')
SUM_UP=$(awk '{s += substr($4,2)} END {print s}' logs/o*-hoards-*.log)
PERCENT_UPDATED=$(printf "%.2f\n" "$(bc -l <<< "$SUM_UP / ($SUM_UP + $SUM_CR) * 100")" )
printf "\nTOTAL\n"
echo "  $SUM_CR abbreviation definitions were new within a committee"
echo "  $SUM_UP definitions matched a known abbreviation with a different long form"
echo "  $PERCENT_UPDATED% of definitions were previously defined with a different long form"

printf "\nNumber of validation errors per error log:\n\n"
# col -b < logs/osi-load-20191217T2236.err.log | grep '400 ' | cut -d']' -f2 | less
for f in logs/o*-load-*.err.log
do
  INVALIDS=$(col -b < "$f" | grep '400 ' | grep -vc 'split into pages' )
  [[ "$INVALIDS" -gt "0" ]] && echo "$f: $INVALIDS clashing definitions"
done
