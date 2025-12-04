import { Button, TextField } from "@mui/material"
import { useEffect, useState } from "react"
import Cloth from "./Cloth"
import Slideshow from "./Slideshow"
import ImageUpload from "./ImageUpload"
import MenuComponent from "./Menu"

const clothing_url = 'https://virtual-tryon-backend-974u.onrender.com'

const Suggestion = () => {
    
    const [metadata, setMetadata] = useState([])

    // sorting
    const [type, setType] = useState(null)
    const [selectedType, setSelectedType] = useState([])
    const [color, setColor] = useState(null)
    const [selectedColor, setSelectedColor] = useState([])
    const [season, setSeason] = useState(null)
    const [selectedSeason, setSelectedSeason] = useState([])
    const [usage, setUsage] = useState(null)
    const [selectedUsage, setSelectedUsage] = useState([])

    const [mode, setMode] = useState('top')
    const [cloth, setCloth] = useState(null)
    const [query, setQuery] = useState('')
    const [result, setResult] = useState(null)

    useEffect(() => {
        if (mode != 'upload') {
            fetch(`${clothing_url}/${mode}s`)
                .then(res => res.json())
                .then(json => {
                    setType([...new Set(json.map((item) => item.articleType))])
                    setColor([...new Set(json.map((item) => item.baseColour))])
                    setSeason([...new Set(json.map((item) => item.season))])
                    setUsage([...new Set(json.map((item) => item.usage))])
                    let img_url = json.map((item) => item.image_url)
                    console.log(img_url.length)
                    // if (selectedType.length != 0 || selectedColor.length != 0 || selectedSeason.length != 0 || selectedUsage.length != 0) {
                    //     img_url = img_url.filter((item) => (
                    //             selectedType.includes(item.articleType) &&
                    //             selectedColor.includes(item.baseColour) && 
                    //             selectedSeason.includes(item.season) &&
                    //             selectedUsage.includes(item.usage)
                    //         ))
                        
                    //     console.log(img_url.length)
                    // }
                    const result = []
                    for (let i = 0; i < 9; i++) {
                        const randomIndex = Math.floor(Math.random() * img_url.length);
                        console.log(randomIndex)
                        const selectedElement = clothing_url + img_url.splice(randomIndex, 1)[0];
                        result.push({'img': selectedElement});
                    }
                    setMetadata(result)
                })
        } else { // mode = 'upload'
            setMetadata(null)
        }
    }, [mode, selectedType, selectedColor, selectedSeason, selectedUsage])

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

    const selectMode = (value) => {
        setMode(value.toLowerCase())
        setCloth(null)
        setResult(null)
    }


    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'row'
            }}
        >
            <div
                style={{
                    height: '100%',
                    width: '100%'
                }}
            >
                {/* <div
                    style={{
                        display: 'flex',
                        flexDirection: 'row'
                    }}
                >
                    <MenuComponent
                        title='Options'
                        values={['Top', 'Bottom', 'Upload']}
                        handleSelect={(value) => selectMode(value)}
                    />

                    {type && 
                        <MenuComponent
                            title='Types'
                            values={type}
                            handleSelect={(value) => setSelectedType(prev => [...prev, value])}
                        />
                    }

                    {color && 
                        <MenuComponent
                            title='Colors'
                            values={color}
                            handleSelect={(value) => setSelectedColor(prev => [...prev, value])}
                        />
                    }

                    {season && 
                        <MenuComponent
                            title='Seasons'
                            values={season}
                            handleSelect={(value) => setSelectedSeason(prev => [...prev, value])}
                        />
                    }

                    {usage && 
                        <MenuComponent
                            title='Usages'
                            values={usage}
                            handleSelect={(value) => setSelectedUsage(prev => [...prev, value])}
                        />
                    }
                </div> */}

                <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                    <span>Filters:</span>
                    {[...selectedType, ...selectedColor, ...selectedSeason, ...selectedUsage].map((f) => {
                        return (
                            <div
                                key={f}
                                style={{
                                    padding: "4px 10px",
                                    borderRadius: "12px",
                                    background: "#eee"
                                }}
                            >
                                {f}
                            </div>
                        )
                    })}
                </div>

                <div
                    style={{
                        height: '100%',
                        width: '100%'
                    }}
                >
                    {metadata ? (
                        <Cloth
                            id='suggestion'
                            itemData={metadata}
                            num_cols={3}
                            handleSelection={(img) => {
                                img = img.substring((clothing_url+'/static/').length, img.length-4)
                                setCloth(img)
                            }}
                            upload={false}
                        />
                    ) : (
                        <div>
                            <ImageUpload
                                handleUpload={(img) => setCloth(img)}
                            />
                        </div>
                    )}
                </div>
            </div>

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    width: '100%'
                }}
            >
                {/* {mode == 'upload' && 
                    <TextField
                        label='enter query'
                        variant='standard'
                        multiline
                        onChange={(e) => {
                            setQuery(e.target.value)
                        }}
                    />
                } */}

                <Button
                    onClick={getSuggestion}
                >
                    Get suggestion
                </Button>

                {result && (
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            maxHeight: '100vh',
                            overflowX: 'scroll'
                        }}
                    >
                        Explanation: {result.explanation}
                        <Slideshow images={result.looks.map((item) => `https://virtual-tryon-backend-974u.onrender.com${item.bottom.image_url}`)}/>
                        {/* {result.looks.map((item) => (
                            <img 
                                key={item.bottom.image_url} 
                                src={`https://virtual-tryon-backend-974u.onrender.com${item.bottom.image_url}`}
                                style={{
                                    width: '100%',
                                    height: '100%'
                                }}
                            />
                        ))} */}
                    </div>
                )}
            </div>
        </div>
    )

}

export default Suggestion