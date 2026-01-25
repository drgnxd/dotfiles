# Unix Philosophy in Detail

## Selected Rules (Doug McIlroy)

1. Small is beautiful.
2. Make each program do one thing well.
3. Build a prototype as soon as possible.
4. Choose portability over efficiency.
5. Store data in flat text files.
6. Use software leverage.
7. Use shell scripts to increase leverage and portability.
8. Avoid captive user interfaces.
9. Make every program a filter.

## Pike's Rules

1. You cannot tell where a program will spend its time.
2. Measure. Do not tune for speed until you measure.
3. Fancy algorithms are slow when n is small.
4. Fancy algorithms have big constants.
5. Data dominates; choose the right data structures first.

## Practical Examples

Good: composable tools
```bash
cat access.log | grep "ERROR" | cut -d' ' -f1 | sort | uniq -c
```

Bad: monolithic tool
```bash
custom_log_analyzer --errors --count --unique access.log
```
