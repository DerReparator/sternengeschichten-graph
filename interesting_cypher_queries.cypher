# Get list of the most-referenced (directly) episodes

MATCH (f:Episode)-[:mentions]->(ep:Episode)
WITH ep,count(f) as mentionCount, collect(f) as mentioningEps
WHERE mentionCount >= 1
RETURN ep,mentioningEps, mentionCount
ORDER BY mentionCount DESC
