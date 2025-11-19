import { Button, TextField } from "@mui/material"
import { useState } from "react"
import Cloth from "./Cloth"


const Suggestion = () => {

    const [query, setQuery] = useState('')

    const getSuggestion = (event) => {
        // get suggestion using query + selected clothing
    }

    return (
        <div
            style={{
                height: '100%',
                width: '100%',
                display: 'flex',
                flexDirection: 'col'
            }}
        >
            <Cloth
                id='suggestion'
                itemData={[]}
                num_cols={5}
            />
            <TextField
                label='enter query'
                variant='standard'
                multiline
                onChange={(e) => {
                    setQuery(e.target.value)
                }}
            />

            <Button
                onClick={getSuggestion}
            >
                Get suggestion
            </Button>
        </div>
    )

}

export default Suggestion