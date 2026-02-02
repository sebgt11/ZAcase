Zangenberg Case "Fortrolige Filer Automatisk BM":

Her kan du se besvarelsen på casen. 

----------------------------------------------------------------------------------------------------
Kort forklaring:

Ideen tackler lidt både den udvidet og originale problemstilling på samme tid. Tankegangen er at lave en simpel Webapp hvor man kan indsætte sin excel fil, en API sender den til backend som kører de "Hemmelige beregninger" og så sender API tilbage til fronten hvor client kan så downloade den nye excel fil. Den her techstack bliver vist på slide 4 i pp.

----------------------------------------------------------------------------------------------------

For at køre koden:

Du skal bare køre køre app.py. så burde den åbne et link i din browser. Jeg har sat en test excel fil ind i folderen også som du kan bruge til at teste. den har bare værdien 50 i celle A1.

----------------------------------------------------------------------------------------------------

Skulle der være problemer med at køre/åbne link:

udkommentere eventuelt

"if __name__ == "__main__":
    threading.Timer(0.8, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)"

og så kør koden manuelt fra terminalen med kommandoen:

"uvicorn app:app --host 0.0.0.0 --port 8000"

og så click på linket i terminalen for at åbne den i browseren.


-----------------------------------------------------------------------------------------------------

Bemærk Hvis der er problemer med at køre koden kan du se hvilke versioner jeg kører på i requirement.txt

-----------------------------------------------------------------------------------------------------

Forklaring af kode:
Strukturen er således,
app.py
engine.py
data
    |Uploads
    |Outputs

app.py: Det er hovedfilen og står for at køre det hele lokalt ved hjælp af uvicorn. Den benytter FastAPI til API kald, den står også for den simple hjemmeside som er lavet med HTML og JavaScript. Så står den for når en excel fil er uploadet og der bliver trykket på knappen så kører den en function som der laver mellemregninger. Mellemregninger ligger i engine.py

engine.py: Den står for mellemregningerne. Det vil sige den står for at load excel filen som man client har givet og så lave en ny med de relevant beregninger, I den her har jeg bare fordoblet værdien af tallet i celle A1 bare for at vise proof of concept.

data: her har man overblik over alle input og output filer hvor de er for givet uuid som navn.

-----------------------------------------------------------------------------------------------------

Viderbyggelse:

Lige nu er det mere en protoype og proof of concept end det er noget andet. Ideen er at man vil lave det til en full on web app med VM, domæne og det hele. Det ville løse problemet med at clienter og inhouse personale kan bruge og dermed er der ingen flaskehals. Og så er det desuden rart at folk ikke skal ud og downloade noget at de bare kan tilgå en hjemmeside. Se slide 5 for TechStack