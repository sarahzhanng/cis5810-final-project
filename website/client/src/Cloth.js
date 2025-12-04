import React, { useContext, useState } from "react";
import { ImageList, ImageListItem, IconButton } from '@mui/material';
import FavoriteIcon from "@mui/icons-material/Favorite";
import ImageUpload from "./ImageUpload";
import { AuthContext } from "./AuthContext";

const Cloth = ({id, itemData, num_cols, handleSelection, upload }) => {
    const { username } = useContext(AuthContext)
    
    const [selected, setSelected] = useState(null);

    const selectImage = (img) => {
        setSelected(img)
        handleSelection(img)
    }

    return (
        <div>
            <ImageList cols={num_cols}>
                {upload && 
                    <ImageListItem
                        onClick={() => {
                            setSelected('uploaded')
                        }}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: selected === "uploaded" ? "3px solid #1976d2" : "3px solid transparent",
                            borderRadius: "8px",
                            padding: "8px",
                            cursor: "pointer",
                            boxSizing: 'border-box'
                        }}
                    >
                        <ImageUpload
                            handleUpload={(img) => {
                                selectImage(img)
                            }}
                        />
                    </ImageListItem>
                }

                {itemData.map((item) => (
                    <ImageListItem
                        key={item.img}
                        onClick={() => selectImage(item.img)}
                        style={{
                            aspectRatio: "1 / 1",
                            width: "100%",
                            overflow: "hidden",
                            border: selected === item.img ? "3px solid #1976d2" : "3px solid transparent",
                            borderRadius: "8px",
                            cursor: "pointer",
                            boxSizing: 'border-box'
                        }}
                    >
    <img 
        src={item.img}
        style={{
            width: "100%",
            height: "100%",
            objectFit: "contain"
        }}
    />
    {username && 
    <IconButton
        // onClick={(e) => { e.stopPropagation(); toggleSave(item.img); }}
        style={{
            position: 'absolute',
            top: 8,
            right: 8,
            // color: savedImages.includes(item.img) ? 'red' : 'white',
            backgroundColor: 'rgba(0,0,0,0.3)',
            borderRadius: '50%'
        }}
    >
        <FavoriteIcon />
    </IconButton>
    }

                    </ImageListItem>
                ))}
            </ImageList>
        </div>
    );
};

export default Cloth;
