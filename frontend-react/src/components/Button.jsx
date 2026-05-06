import React from 'react'
import { Link } from 'react-router-dom'

const Button = (props) => {
  const classes = ['btn', props.class, props.className].filter(Boolean).join(' ')
  return <Link className={classes} to={props.url}>{props.text}</Link>
}

export default Button