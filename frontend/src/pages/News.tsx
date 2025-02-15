import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Box,
  TextField,
  Button,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface NewsItem {
  id: string;
  title: string;
  content: string;
  created_at: string;
}

const News = () => {
  const { user } = useAuth();
  const [news, setNews] = useState<NewsItem[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/news');
      setNews(response.data);
    } catch (error) {
      console.error('Error fetching news:', error);
    }
  };

  const handleSubmitNews = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/news', {
        title,
        content,
      });
      setTitle('');
      setContent('');
      fetchNews();
    } catch (error) {
      console.error('Error creating news:', error);
    }
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Market News
      </Typography>

      {user?.role === 'admin' && (
        <Box component="form" onSubmit={handleSubmitNews} sx={{ mb: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Create News
              </Typography>
              <TextField
                fullWidth
                label="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                margin="normal"
                required
                multiline
                rows={4}
              />
              <Button
                type="submit"
                variant="contained"
                color="primary"
                sx={{ mt: 2 }}
              >
                Publish News
              </Button>
            </CardContent>
          </Card>
        </Box>
      )}

      <Grid container spacing={3}>
        {news.map((item) => (
          <Grid item xs={12} key={item.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {item.title}
                </Typography>
                <Typography color="textSecondary" gutterBottom>
                  {new Date(item.created_at).toLocaleDateString()}
                </Typography>
                <Typography variant="body1">{item.content}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

export default News;
