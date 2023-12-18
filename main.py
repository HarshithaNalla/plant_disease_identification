from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from torchvision import transforms
from fastapi.responses import HTMLResponse
from PIL import Image
import io
from torchvision import transforms, models
import pickle
import uvicorn  # Import uvicorn for running the FastAPI app
import os
from google.cloud import firestore 
# Use the path to the JSON key file you downloaded
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./key.json"

# Initialize Firestore client
db = firestore.Client()


app = FastAPI()

class_labels = [
    'Apple__Apple_scab', 'Apple_Black_rot', 'Apple_Cedar_apple_rust', 'Apple_healthy', 'Blueberry_healthy',
    'Cherry(including_sour)__Powdery_mildew', 'Cherry(including_sour)__healthy',
    'Corn(maize)__Cercospora_leaf_spot Gray_leaf_spot', 'Corn(maize)__Common_rust',
    'Corn_(maize)__Northern_Leaf_Blight', 'Corn(maize)__healthy', 'Grape_Black_rot', 'Grape_Esca(Black_Measles)',
    'Grape__Leaf_blight(Isariopsis_Leaf_Spot)', 'Grape__healthy', 'Orange_Haunglongbing(Citrus_greening)',
    'Peach__Bacterial_spot', 'Peach_healthy', 'Pepper,_bell_Bacterial_spot', 'Pepper,_bell_healthy',
    'Potato_Early_blight', 'Potato_Late_blight', 'Potato_healthy', 'Raspberry_healthy', 'Soybean_healthy',
    'Squash_Powdery_mildew', 'Strawberry_Leaf_scorch', 'Strawberry_healthy', 'Tomato_Bacterial_spot',
    'Tomato_Early_blight', 'Tomato_Late_blight', 'Tomato_Leaf_Mold', 'Tomato_Septoria_leaf_spot',
    'Tomato_Spider_mites Two-spotted spider mite', 'Tomato_Target_Spot', 'Tomato_Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato_Tomato_mosaic_virus', 'Tomato__healthy'
]

with open('rresnet18_model.pkl', 'rb') as f:
    model = pickle.load(f)

model.eval()

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
])


def get_class_label(class_index):
    return class_labels[class_index]


def predict_image(img):
    image = transform(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(image)
    _, predicted = torch.max(outputs, 1)
    class_index = predicted.item()
    class_label = get_class_label(class_index)
    return {"class_index": class_index, "class_label": class_label}

def get_disease_information_by_name(disease_name):
    try:
        query = db.collection('plantdisease').where('name', '==', disease_name)
        docs = query.stream()

        for doc in docs:
            return doc.to_dict()

        # If no matching document is found
        return None
    except Exception as e:
        print("Firestore error:", e)
        return None



@app.get('/', response_class=HTMLResponse)
def web():
    with open("main.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


# Create a "templates" directory and put your HTML template in it
templates = Jinja2Templates(directory="templates")


@app.post('/img/', response_class=HTMLResponse)
async def predict(request: Request, file: UploadFile):
    try:
        image = Image.open(io.BytesIO(await file.read()))
        prediction = predict_image(image)

        disease_name = prediction["class_label"]
        print("Disease Name:", disease_name)  # Added print statement
        disease_info = get_disease_information_by_name(disease_name)
        print("Disease Info:", disease_info)  # Added print statement

        if disease_info:
            return templates.TemplateResponse("prediction_template.html", {"request": request, "class_label": disease_name, "disease_info": disease_info})
        else:
            return {"error": "Disease not found."}
    except Exception as e:
        return {"error": str(e)}


@app.post('/report')
async def report_image(fileUrl: str):
    try:
        # Store the image URL in Firebase
        db.collection('reportedImages').add({'image_url': fileUrl})
        return {"message": "Image reported successfully!"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)