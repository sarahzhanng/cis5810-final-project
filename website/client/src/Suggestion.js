import React, { useEffect, useState } from "react";
import { Button, Dropdown, DropdownButton } from "react-bootstrap";
import Cloth from "./Cloth";
import Slideshow from "./Slideshow";
import ImageUpload from "./ImageUpload";

const clothing_url = 'https://virtual-tryon-backend-974u.onrender.com';

const Suggestion = () => {
  const [metadata, setMetadata] = useState([]);
  const [mode, setMode] = useState('tops');
  const [cloth, setCloth] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (mode !== 'upload') {
      fetch(`${clothing_url}/${mode}`)
        .then(res => res.json())
        .then(json => {
          json = json.map(item => item.image_url);
          const result = [];
          for (let i = 0; i < 9; i++) {
            const randomIndex = Math.floor(Math.random() * json.length);
            const selectedElement = clothing_url + json.splice(randomIndex, 1)[0];
            result.push({ img: selectedElement });
          }
          setMetadata(result);
        });
    } else {
      setMetadata(null);
    }
  }, [mode]);

  const getSuggestion = (event) => {
        // get suggestion using query + selected clothing
        if (cloth != null) {
            if (mode == 'tops') {
                const data = {
                    "top_id": cloth
                }
                fetch(`${clothing_url}/generate_looks_from_top`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                    .then(res => res.json())
                    .then(json => {
                        console.log(json)
                        setResult(json)
                    })
            } else if (mode == 'top') {
                const data = {
                    "top_id": cloth
                }
                fetch(`${clothing_url}/generate_looks_from_top`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                    .then(res => res.json())
                    .then(json => {
                        console.log(json)
                        setResult(json)
                    })
            } else if (mode == 'bottom') {
                const data = {
                    "bottom_id": cloth
                }
                fetch(`${clothing_url}/generate_looks_from_bottom`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                    .then(res => res.json())
                    .then(json => {
                        console.log(json)
                        setResult(json)
                    })
            } else {
                fetch(cloth)
                    .then(res => res.blob())
                    .then(blob => {
                        const file = new File([blob], 'image.png', {type: 'png'})
                        const formData = new FormData()
                        formData.append("file", file, "image.png")
                        return fetch(`${clothing_url}/suggest_from_photo`, {
                            method: 'POST',
                            body: formData
                        })
                    })
                    .then(res => res.json())
                    .then(json => {
                        console.log(json)
                        setResult(json)
                    })

            }
        }
    }

  return (
    <div className="container-fluid my-4" style={{ height: "calc(100vh - 2rem)" }}>
      <div className="row h-100 gx-4">

        {/* Left half */}
        <div className="col-12 col-md-6 d-flex flex-column h-100">
          <div className="mb-3 d-flex justify-content-start">
            <DropdownButton title="Options" variant="success">
              <Dropdown.Item onClick={() => setMode('tops')}>Top</Dropdown.Item>
              <Dropdown.Item onClick={() => setMode('bottoms')}>Bottom</Dropdown.Item>
              <Dropdown.Item onClick={() => setMode('upload')}>Upload</Dropdown.Item>
            </DropdownButton>
          </div>

          <div className="flex-fill d-flex">
            {metadata ? (
              <Cloth
                itemData={metadata}
                num_cols={3}
                handleSelection={(img) => {
                  img = img.substring((clothing_url + '/static/').length, img.length - 4);
                  setCloth(img);
                }}
                upload={false}
              />
            ) : (
              <div className="border p-3 rounded w-100 d-flex justify-content-center align-items-center">
                <ImageUpload handleUpload={(img) => setCloth(img)} />
              </div>
            )}
          </div>
        </div>

        {/* Right half */}
        <div className="col-12 col-md-6 d-flex flex-column h-100">
          <div className="mb-3">
            <Button variant="primary" onClick={getSuggestion} className="w-100">
              Get Suggestion
            </Button>
          </div>

          {result && (
            <div className="flex-fill d-flex flex-column">
              <div className="mb-2 p-2 bg-light border rounded">
                <strong>Explanation:</strong> {result.explanation}
              </div>
              <div className="flex-fill">
                <Slideshow
                  images={result.looks.map(
                    (item) => `${clothing_url}${item.bottom.image_url}`
                  )}
                />
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Suggestion;
